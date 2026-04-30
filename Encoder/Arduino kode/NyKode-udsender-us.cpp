#include <Arduino.h>

const int pinA = 2; 
const int pinB = 3; 

// LOCKOUT: 400us debounce limit
const unsigned long DEBOUNCE_MICROS = 400; 

volatile unsigned long lastPulseTime = 0;

// --- 32-Sample Moving Average Variables ---
const int WINDOW_SIZE = 256; // must be a power of 2 for bitwise wraparound (2,4,8,16,32,64,128,256...)
volatile unsigned long delayHistory[WINDOW_SIZE] = {0};
volatile int delayIndex = 0;
volatile bool bufferFull = false; 

volatile unsigned long runningSum = 0;
volatile unsigned long avgDelayMicros = 0;

void readEncoder(); 

void setup() {
  Serial.begin(115200); 
  
  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  
  attachInterrupt(digitalPinToInterrupt(pinA), readEncoder, RISING);
}

void loop() {
  // Serial Monitor handling without the slow 'String' object
  static char serialBuffer[16];
  static byte bufferIndex = 0;

  if (Serial.available() > 0) {
    char c = Serial.read();
    
    // If we hit a newline, process the command
    if (c == '\n' || c == '\r') {
      serialBuffer[bufferIndex] = '\0'; // Terminate string
      
      if (strcmp(serialBuffer, "avg") == 0) {
        // Safely grab the variables from the interrupt
        noInterrupts();
        unsigned long currentAvg = avgDelayMicros;
        unsigned long timeSinceLastPulse = micros() - lastPulseTime;
        interrupts();

        // If no pulses have happened for over 1 second, it has stopped
        if (timeSinceLastPulse > 1000000UL || currentAvg == 0) {
          Serial.println(F("Stopped (0 us)")); // F() macro saves RAM
        } else {
          Serial.print(currentAvg);
          Serial.println("");
        }
      }
      bufferIndex = 0; // Reset buffer for next command
    } 
    else if (bufferIndex < 15) {
      serialBuffer[bufferIndex++] = c;
    }
  }
}

// ISR: Blazing Fast Implementation
void readEncoder() {
  unsigned long now = micros();
  unsigned long dt = now - lastPulseTime;

  // 1. Time-gate: Reject if too soon after last pulse
  if (dt < DEBOUNCE_MICROS) return;

  // 2. Sustained Sampling: Direct Port Manipulation
  // (PIND & 0x04) instantly checks the physical state of Pin 2 on Uno.
  for(int i = 0; i < 10; i++) {
    if (!(PIND & 0x04)) return; 
  }

  // 3. Update the 32-value Circular Buffer
  if (dt < 1000000UL) { 
    runningSum -= delayHistory[delayIndex];
    delayHistory[delayIndex] = dt;
    runningSum += dt;
    
    // Fast Bitwise Wraparound: 31 in binary is 011111. 
    // This instantly wraps 32 back to 0 without an 'if' statement.
    delayIndex = (delayIndex + 1) & 31; 
    
    if (!bufferFull && delayIndex == 0) {
      bufferFull = true;
    }

    // Fast division
    if (bufferFull) {
      // Bitshifting right by 5 is identical to dividing by 32, but takes 1 clock cycle
      avgDelayMicros = runningSum >> 5; 
    } else if (delayIndex > 0) {
      avgDelayMicros = runningSum / delayIndex; 
    }
  }
  
  lastPulseTime = now;
}