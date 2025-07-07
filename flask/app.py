import serial
import sqlite3
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
import threading

#Flask App Initialization
app = Flask(__name__)

#Database global variable
DATABASE = 'spice_weight_data.db'

#Define USB and transmission speed to match Arduin
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600 

#Function to connect to database
def get_db_connection():
    
    conn = sqlite3.connect(DATABASE)
    return conn

#Function to initialize the database
def initialize_db():
    
	#Connect to database and create table if not existing already
    try:
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
                       
            CREATE TABLE IF NOT EXISTS spice_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                weight REAL NOT NULL 
            )
                       
        ''')
        
        conn.commit()
        print("Spice weight database initialized.")

	#Database exception handling       
    except sqlite3.Error as e:
        
        print(f"Database error: {e}")

	#Close database connection      
    finally:
        
        if conn:
            
            conn.close()

#Add weight reading to database
def add_weight_reading(weight):
    
	#Reset conn to nothing to ensure less issues
    conn = None
    
	#Add weight into table and print it out to check
    try:
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO spice_readings (weight) VALUES (?)", (weight,))
        conn.commit()
        print(f"Recorded Weight: {weight} at {datetime.now()}")

	#Database exception handling
    except sqlite3.Error as e:
        
        print(f"Database error when adding weight reading: {e}")

	#Close the database connection    
    finally:
        
        if conn:
            
            conn.close()

#Web App Functions
#Get the most recent weight reading from the database
def get_latest_reading():

    conn = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()
        #Order by ID descending and get the first result
        cursor.execute("SELECT weight, timestamp FROM spice_readings ORDER BY id DESC LIMIT 1")
        reading = cursor.fetchone() # Fetches one record or None
        return reading
    
    except sqlite3.Error as e:

        print(f"Database error when fetching latest reading: {e}")
        return None
    
    finally:

        if conn:
            conn.close()

#Background Task for Reading Serial Data
def start_serial_reader():

    ser = None
    
    try:
       
        #Establish serial connection with the Arduino
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
       
        #Wait for the Arduino to reset after establishing the connection
        time.sleep(2)
        print(f"Connected to Arduino on {SERIAL_PORT}. Waiting for weight data...")

        #Read data from the serial port
        while True:
           
            if ser.in_waiting > 0:
                
                #Format output
                line = ser.readline().decode('utf-8').strip()

                if line:
                    try:
                        #Convert to float
                        weight = float(line)
                        #Add the weight reading to the database
                        add_weight_reading(weight)
                    except ValueError:
                        print(f"Removed non-numeric value: '{line}'")
    
    except serial.SerialException as e:
        print(f"Serial Error: {e}")
        print(f"Could not connect to {SERIAL_PORT}. Please check the connection.")
    
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")

    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial connection closed.")

#Flask Route

@app.route('/')
def index():

    return render_template('index.html')

#Convert to JSON for output
@app.route('/latest_weight')
def latest_weight_json():

    reading = get_latest_reading()
    if reading:

        return jsonify({'weight': reading[0], 'timestamp': reading[1]})
    else:

        return jsonify({'weight': 'N/A', 'timestamp': 'N/A'})

if __name__ == '__main__':

    initialize_db()
    #Start the serial reading function in a separate, background thread
    serial_thread = threading.Thread(target=start_serial_reader, daemon=True)
    serial_thread.start()
   
    #Run app and use_reloader=False = run app once
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
