/*
  PSA Automotive LCD Basic Speedometer Example
  Demonstrates how to initialize the LCD, clear the memory buffers,
  and update the main 3-digit speed display safely.
  
  Target Hardware: ESP32 / Arduino
  Tested wiring (based on our actual bench tests):
  LCD Pins: VDD(3.3V), GND, SDA, SCL, V_LCD(5V)
*/

#include <Wire.h>

#define PIN_SDA 9
#define PIN_SCL 7
#define LCD_ADDR 0x38

// Hardware limits for PCF8576 
#define BUFFER_SIZE 40
uint8_t lcd_buffer[BUFFER_SIZE] = {0};

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Based on our actual tests, 100kHz works correctly with this panel
  Wire.begin(PIN_SDA, PIN_SCL, 100000);

  initLCD();
  Serial.println("LCD Initialized.");
}

void loop() {
  // Simple sweeping animation 0 to 299 Km/h
  for(int speed = 0; speed <= 299; speed++) {
    memset(lcd_buffer, 0, sizeof(lcd_buffer));
    displayNumber(speed);
    updateLCD_Main();
    delay(50); // Frame delay
  }
}

// ==================== I2C Functions ====================
void initLCD() {
  // Init Sub-Chip (0xCE) and clear memory
  Wire.beginTransmission(LCD_ADDR);
  Wire.write(0x80); Wire.write(0x48); // Device Select
  Wire.write(0x80); Wire.write(0xC8); // Mode: 1:4 Mux, 1/3 Bias (MANDATORY)
  Wire.write(0x80); Wire.write(0x70); // Blink Off
  Wire.write(0x80); Wire.write(0xCE); // Select Sub-Chip
  Wire.write(0x80); Wire.write(0x00); // Reset Pointer
  Wire.write(0x40);                   // Start writing
  for(int i = 0; i < BUFFER_SIZE; i++) Wire.write(0x00);
  Wire.endTransmission();
  delay(10);

  // Init Main-Chip (0xE0)
  Wire.beginTransmission(LCD_ADDR);
  Wire.write(0x80); Wire.write(0x48); 
  Wire.write(0x80); Wire.write(0xC8); 
  Wire.write(0x80); Wire.write(0x70); 
  Wire.write(0x80); Wire.write(0xE0); // Select Main-Chip
  Wire.write(0x80); Wire.write(0x00); // Reset Pointer
  Wire.write(0x40);                   
  for(int i = 0; i < BUFFER_SIZE; i++) Wire.write(0x00);
  Wire.endTransmission();
  delay(10);
}

void updateLCD_Main() {
  // CRITICAL: Always explicitly select 0xE0 and reset pointer to 0x00 
  // before a 40-byte transmission to prevent cascaded memory overflow.
  Wire.beginTransmission(LCD_ADDR);
  Wire.write(0x80); Wire.write(0xE0); 
  Wire.write(0x80); Wire.write(0x00); 
  Wire.write(0x40);
  for(int i = 0; i < BUFFER_SIZE; i++) {
    Wire.write(lcd_buffer[i]);
  }
  Wire.endTransmission();
}

void setSegment(int byteIndex, int bitIndex) {
  if(byteIndex >= 0 && byteIndex < BUFFER_SIZE && bitIndex >= 0 && bitIndex <= 7) {
    lcd_buffer[byteIndex] |= (1 << bitIndex);
  }
}

// ==================== Display Logic ====================
void displayDigit1(int num) {
  // Hundreds digit: Supports only 1 or 2
  if (num == 1) {
    setSegment(18, 5); setSegment(17, 1); setSegment(18, 7);
  } else if (num == 2) {
    setSegment(18, 5); setSegment(17, 1); setSegment(18, 4); 
    setSegment(17, 0); setSegment(17, 3);
  }
}

void displayDigit2(int num) {
  // Tens digit
  if(num==0||num==2||num==3||num==5||num==6||num==7||num==8||num==9) setSegment(18, 1); // 2a
  if(num==0||num==4||num==5||num==6||num==8||num==9) setSegment(19, 5); // 2b
  if(num==0||num==1||num==2||num==3||num==4||num==7||num==8||num==9) setSegment(19, 1); // 2c
  if(num==0||num==2||num==4||num==5||num==6||num==8||num==9) setSegment(18, 3); // 2d
  if(num==2||num==3||num==4||num==5||num==6||num==8||num==9) setSegment(19, 3); // 2e
  if(num>=0 && num<=9) setSegment(18, 0); // 2f
  if(num==0||num==2||num==6||num==8) setSegment(19, 7); // 2g
  if(num==0||num==1||num==3||num==4||num==5||num==6||num==7||num==8||num==9) setSegment(19, 0); // 2h
  if(num==0||num==2||num==3||num==5||num==6||num==8||num==9) setSegment(18, 2); // 2i
  if(num==0||num==1||num==2||num==3||num==4||num==5||num==6||num==7||num==8||num==9) setSegment(19, 2); // 2j
}

void displayDigit3(int num) {
  // Ones digit
  if(num==0||num==2||num==3||num==5||num==6||num==7||num==8||num==9) setSegment(20, 5); // 3a
  if(num==0||num==4||num==5||num==6||num==8||num==9) setSegment(20, 1); // 3b
  if(num==0||num==1||num==2||num==3||num==4||num==7||num==8||num==9) setSegment(21, 5); // 3c
  if(num==0||num==2||num==4||num==5||num==6||num==8||num==9) setSegment(20, 7); // 3d
  if(num==2||num==3||num==4||num==5||num==6||num==8||num==9) setSegment(21, 7); // 3e
  if(num>=0 && num<=9) setSegment(20, 4); // 3f
  if(num==0||num==2||num==6||num==8) setSegment(20, 3); // 3g
  if(num==0||num==1||num==3||num==4||num==5||num==6||num==7||num==8||num==9) setSegment(21, 4); // 3h
  if(num==0||num==2||num==3||num==5||num==6||num==8||num==9) setSegment(20, 6); // 3i
  if(num==0||num==1||num==2||num==3||num==4||num==5||num==6||num==7||num==8||num==9) setSegment(21, 6); // 3j
}

void displayNumber(int number) {
  if(number < 0) number = 0;
  if(number > 299) number = 299;

  if(number < 10) {
    displayDigit2(number);
  }
  else if(number < 100) {
    displayDigit2(number / 10);
    displayDigit3(number % 10);
  }
  else {
    displayDigit1(number / 100);
    displayDigit2((number / 10) % 10);
    displayDigit3(number % 10);
  }
  
  // Enable "Km/h" text
  setSegment(23, 2); 
}
