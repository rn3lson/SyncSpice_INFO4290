#include "HX711.h"

//Define the pins for the HX711 module
#define DOUT_PIN 3
#define SCK_PIN  2

//Instantiate the scale from the library
HX711 scale;

void setup() {

    //Set baud rate (tranmission speed)
    Serial.begin(9600);

    //Initialize the pins on the Hx711           
    scale.begin(DOUT_PIN, SCK_PIN);
  
  //Delay at the beginning to initalize
  delay(1000);

  //Tare scale with average of readings
  scale.tare();

}

void loop() {

    //Check if the scale/load cell/HX711 is ready
    if (scale.is_ready()) {   

        //Put what is read into a weight varible and print
        float weight = scale.read(); // Read the raw data from the HX711
        Serial.print("Weight Data: ");       // Print prefix "Data: "
        Serial.println(weight);     // Output the raw reading value

    } 
    
    //Check if HX711 is connect and pins are ready
    else {

        Serial.println("HX711 not ready: Check physical connection or restart.");

  }
  
  //Set delay between readings
  delay(2000);

}