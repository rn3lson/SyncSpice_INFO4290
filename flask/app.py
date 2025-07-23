import serial
import sqlite3
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import threading

#Flask App Initialization
app = Flask(__name__)

#Database global variable
DATABASE = 'spice_weight_data.db'

#Define USB and transmission speed to match Arduin
SERIAL_PORT = 'COM3' 
BAUD_RATE = 9600 

#Define a threshold for zeroing out small changes around the tare point
WEIGHT_THRESHOLD = 0.5

#Global serial object
ser = None

#Global tare offset and tare lock to ensure multiple threads can access
TARE_OFFSET = 0.0
tare_lock = threading.Lock()

#Function to connect to database
def get_db_connection():
    
    conn = sqlite3.connect(DATABASE)
    return conn

#Function to initialize the database
def initialize_db():
    
    #Close connection when need
    with get_db_connection() as conn:

        try:

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

        except sqlite3.Error as e:

            print(f"Database error during initialization: {e}")

#Add weight reading to database
def add_weight_reading(weight):

    with get_db_connection() as conn:

        try:

            cursor = conn.cursor()
            cursor.execute("INSERT INTO spice_readings (weight) VALUES (?)", (weight,))
            conn.commit()
            print(f"Recorded Weight: {weight} at {datetime.now()}")

        except sqlite3.Error as e:

            print(f"Database error when adding weight reading: {e}")

#Web App Functions
#Get the most recent weight reading from the database
def get_latest_reading():

    with get_db_connection() as conn:

        cursor = conn.cursor()
        #Order by ID descending and get the first result
        cursor.execute("SELECT weight, timestamp FROM spice_readings ORDER BY id DESC LIMIT 1")
        reading = cursor.fetchone() # Fetches one record or None
        return reading
    

#Background Task for Reading Serial Data
def start_serial_reader():

    global ser, TARE_OFFSET, tare_lock
    
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
                        raw_weight = float(line)

                        #Ensure only one thread can access at a time.
                        with tare_lock:
                            #Apply the tare offset to the raw weight
                            adjusted_weight = raw_weight - TARE_OFFSET
                        
                        #If the adjusted weight is within the noise threshold, treat it as zero.
                        #creates a stable zero point after taring.
                        if abs(adjusted_weight) < WEIGHT_THRESHOLD:

                            adjusted_weight = 0.0

                        #Add the weight reading to the database
                        add_weight_reading(adjusted_weight)

                    #Remove the calibration feedback from the output.    
                    except ValueError:

                        print(f"Removed non-numeric value: '{line}'")
    
    #Throw error if serial port not reachable.
    except serial.SerialException as e:

        print(f"Serial Error: {e}")
        print(f"Could not connect to {SERIAL_PORT}. Please check the connection.")
    

    finally:

        if ser and ser.is_open:

            ser.close()
            print("Serial connection closed.")

#Flask Routes
@app.route('/calibrate', methods=['POST'])
def calibrate_scale():

    """Sends the calibration command 'c' to the Arduino."""
    global ser
    if ser and ser.is_open:
        try:

            #End the character 'c' (adapted original pre Json)
            ser.write(b'c') 
            message = "Calibration command sent. Please follow the instructions in the application terminal."
            print(f"\n--{message}--\n")
            return jsonify({'status': 'success', 'message': message})
        
        #Throw exception if c is not given
        except Exception as e:

            error_message = f"Failed to send calibration command: {e}"
            print(error_message)
            return jsonify({'status': 'error', 'message': error_message}), 500
        
    else:

        #Handles if the serial port isn't open
        return jsonify({'status': 'error', 'message': 'Serial connection not available.'}), 503

@app.route('/tare', methods=['POST'])
def tare_scale():

    """Reads the latest weight and sets it as the new zero offset in software."""
    global TARE_OFFSET, tare_lock
    
    #Get the last reading from the database to calculate the actual raw weight
    last_reading = get_latest_reading()

    if last_reading:

        #To get the raw weight, we add the old offset back.
        last_adjusted_weight = last_reading[0]
        
        with tare_lock:

            #Last reading was TARE_OFFSET + last_adjusted_weight
            #Set this raw weight as the new offset.
            new_offset = TARE_OFFSET + last_adjusted_weight
            TARE_OFFSET = new_offset
            print(f"New tare offset set to: {TARE_OFFSET:.2f}g")

        return jsonify({'status': 'success', 'message': f'Scale zeroed. New offset is {TARE_OFFSET:.2f}g.'})
    
    else:

        return jsonify({'status': 'error', 'message': 'No weight yet.'}), 500

#Flask Routes
@app.route('/')
def home():

    """Renders the home/welcome page."""
    return render_template('home.html')

@app.route('/scale')
def scale_page():

    """Renders the main scale interface page."""
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
