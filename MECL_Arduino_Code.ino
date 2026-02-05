/* MASTER FIRMWARE: PCF8591 SINGLE CHIP */
#include <Wire.h>

#define PCF_ADDR 0x48 

void setup() {
  Serial.begin(115200); // Fast Serial
  Wire.begin();
  Wire.setClock(400000); // Fast I2C
  
  Serial.println("READY: PCF8591");
}

void loop() {
  if (Serial.available() > 0) {
    // 1. Receive Value from PC
    String str = Serial.readStringUntil('\n');
    int val = str.toInt();
    if (val > 255) val = 255; 

    // 2. WRITE to DAC (Pin 15)
    Wire.beginTransmission(PCF_ADDR);
    // Control Byte 0x40: Enable Analog Output
    Wire.write(0x40); 
    Wire.write(val);  // Send value
    Wire.endTransmission();

    // 3. READ from ADC (Pin 1)
    // We send Control Byte 0x40 AGAIN to keep DAC ON while reading Ch0
    Wire.beginTransmission(PCF_ADDR);
    Wire.write(0x40); 
    Wire.endTransmission();

    // Request Data
    Wire.requestFrom(PCF_ADDR, 2);
    Wire.read();             // Dummy read (old data)
    int captured = Wire.read(); // New valid data

    // 4. Send Back
    Serial.print(val);
    Serial.print(",");
    Serial.println(captured);
  }
}