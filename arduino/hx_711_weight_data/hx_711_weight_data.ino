#include "HX711.h"

//Define the pins for the HX711 module
#define DOUT_PIN 3
#define SCK_PIN  2

#define CALIBRATION_WEIGHT_GRAMS 50.0f 

//Instantiate the scale from the library.
HX711 scale;

void setup() {

    //Set baud rate (tranmission speed).
    Serial.begin(9600);

    //Initialize the pins on the Hx711.        
    scale.begin(DOUT_PIN, SCK_PIN);

    Serial.println("HX711 Initialized.");
    Serial.println("Ensure scale is empty. Taring...");
    delay(2000);

    //Tare the scale with 20 readings for stability to set the zero reference.
    scale.tare(20); 
    Serial.println("Tare complete. Scale zeroed.");
    delay(2000);

    //Give time to place the weight and for the load cell to settle
    Serial.println("Place the " + String(CALIBRATION_WEIGHT_GRAMS, 1) + "g calibration weight on the scale.");
    Serial.println("Waiting for 8 seconds to allow placement and for readings to stabilize...");
    delay(8000); 

    if (scale.is_ready()) {

        Serial.println("Reading value for calibration...");
        
        //Get an average of 10 raw ADC readings for the calibration weight.
        //This value is relative to the tare point.
        long number_readings = scale.get_value(10); 
        Serial.print("Raw ADC value for ");
        Serial.print(CALIBRATION_WEIGHT_GRAMS, 1);
        Serial.print("g: ");
        Serial.println(number_readings);

        //Calculate the calibration factor, cast so it doesn't trim decimals
        float calibration_factor = (float)number_readings / CALIBRATION_WEIGHT_GRAMS;
        scale.set_scale(calibration_factor);

        //Print more refined.
        Serial.print("Calibration factor calculated and set: ");
        Serial.println(calibration_factor, 4); 
        Serial.println("Calibration complete. You can remove the calibration weight.");
        delay(2000);

        Serial.println("The scale will now output weight in grams.");

        //Give time to remove the weight
        Serial.println("Waiting for 5seconds before final tare...");
        delay(5000); 
        Serial.println("Taring scale again to set zero with new calibration...");

         //Tare again now that scale factor is set
        scale.tare(20);
        Serial.println("Scale re-zeroed. Ready to measure.");

    } 
    
    else {

        Serial.println("HX711 not ready during calibration. Check connections and restart.");
        
        //Stop execution if calibration fails
        while(1) { 

            delay(1000); 

        }
    }
}

void loop() {

    //Check if the scale/load cell/HX711 is ready
    if (scale.is_ready()) {   

        // Read the weight in grams, using the calibration factor.
        // Get an average of 10 readings for stability.
        float weight = scale.get_units(10); 
      
        Serial.println(weight, 2); // Print only the numeric weight value for easy parsing

    } 

    //Check if HX711 is connect and pins are ready
    else {

        Serial.println("HX711 not ready: Check physical connection or restart.");

    }
  
    //Set delay between readings
    delay(500);

}