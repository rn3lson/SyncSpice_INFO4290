import serial
import sqlite3
import time
from datetime import datetime 

#Database global variable
DATABASE = 'spice_weight_data.db'

#Define USB and transmission speed to match Arduino
SERIAL_PORT = '/dev/ttyACM0' 
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


#Test output/app before UI

#Still to implement: 
#	1. Serial in and test the data into the db in the console 2. Develop HTML/Front end.
if __name__ == '__main__':
    
    initialize_db()
