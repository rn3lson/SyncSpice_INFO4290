#include "HX711.h"

//Define the pins for the HX711 module
#define DOUT_PIN 3
#define SCK_PIN  2

//Define the known weight for calibration weight as a float, global variable.
#define CALIBRATION_WEIGHT_GRAMS 50.0f

//Hardcode original cali factor.
#define CALIBRATION_FACTOR -423.0f

//Instantiate the scale from the library.
HX711 scale;

void runCalibration() {

    Serial.println("--Starting Recalibration--");
    Serial.println("Ensure scale is empty. Taring...");
    delay(2000);

    //Tare the scale with 20 readings for stability to set the zero reference.
    scale.tare(20);
    Serial.println("Tare complete.");
    delay(2000);

    //Give time to place the weight and for the load cell to settle
    Serial.println("Place the " + String(CALIBRATION_WEIGHT_GRAMS, 1) + "g calibration weight on the scale.");
    Serial.println("Waiting for 8 seconds to allow placement and for readings to stabilize...");
    delay(8000);

    if (scale.is_ready()) {

        Serial.println("Reading value for calibration...");

        //Get an average of 20 raw ADC readings for the calibration weight.
        long number_readings = scale.get_value(20);
        Serial.print("Raw ADC value for ");
        Serial.print(CALIBRATION_WEIGHT_GRAMS, 1);
        Serial.print("g: ");
        Serial.println(number_readings);

        //Calculate the new calibration factor
        float new_calibration_factor = (float)number_readings / CALIBRATION_WEIGHT_GRAMS;
        scale.set_scale(new_calibration_factor);

        Serial.print("New calibration factor calculated and set: ");
        Serial.println(new_calibration_factor, 4);
        Serial.println("Calibration complete. You can remove the calibration weight.");
        delay(2000);

        Serial.println("Waiting for 5 seconds before final tare...");
        delay(5000);
        scale.tare(20);
        Serial.println("Scale re-zeroed. Ready to measure.");
        Serial.println("--Recalibration Finished--");

    } 
    
    else {

        Serial.println("HX711 not ready during calibration. Check connections and restart.");

    }
}

void setup() {

    //Set baud rate (tranmission speed).
    Serial.begin(9600);

    //Initialize the pins on the HX711
    scale.begin(DOUT_PIN, SCK_PIN);

    Serial.println("HX711 Initialized.");
    
    //Set the scale factor using the hardcoded value
    scale.set_scale(CALIBRATION_FACTOR);
    Serial.println("Using hardcoded calibration factor.");

    //Tare the scale to set the zero reference
    Serial.println("Taring...");
    scale.tare(20);
    Serial.println("Tare complete. Scale is ready.");

}

void loop() {

    //Check if the scale/load cell/HX711 is ready
    if (scale.is_ready()) {   

        //Check for an incoming command to recalibrate
        if (Serial.available() > 0) {

            char command = Serial.read();
            if (command == 'c') {
                runCalibration();

            }

        } 
        
        else {

            //If no command, just read and print the weight
            //Get an average of readings for better stability.
            float weight = scale.get_units(5);
            Serial.println(weight, 2);

        }

    } else {

        Serial.println("HX711 not ready: Check physical connection or restart.");

    }
  
    //Set delay between readings
    delay(1000);

}
