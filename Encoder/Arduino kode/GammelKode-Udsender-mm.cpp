#include <Arduino.h>

const int pinA = 2; 
const int pinB = 3; 
const float PPR = 2000.0; 
const float RADIUS = 0.0275; 
const float CIRCUMFERENCE_MM = 2.0 * PI * RADIUS * 1000.0;

// LOCKOUT: 400us is the "Sweet Spot" for 190mm/s max speed
const unsigned long DEBOUNCE_MICROS = 400; 

volatile long encoderPosition = 0;
volatile unsigned long lastPulseTime = 0;
float avgVelocity = 0.0;

const int WINDOW_SIZE = 10; 
long posHistory[WINDOW_SIZE] = {0};
int historyIndex = 0;
bool bufferFull = false;
unsigned long lastHistoryUpdate = 0;

void readEncoder(); 

void setup() {
  Serial.begin(115200); 
  
  // Internal pullups + your 6.8nF capacitors = Strong Hardware Filter
  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  
  lastHistoryUpdate = millis(); 
  attachInterrupt(digitalPinToInterrupt(pinA), readEncoder, RISING);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // 10-Second Average Logic
  if (currentMillis - lastHistoryUpdate >= 1000) {
    lastHistoryUpdate += 1000; 
    noInterrupts();
    long currentPos = encoderPosition;
    interrupts();

    long oldestPos = posHistory[historyIndex];
    posHistory[historyIndex] = currentPos;

    if (bufferFull) {
      long deltaPos = currentPos - oldestPos;
      float avgPPS = (float)deltaPos / WINDOW_SIZE; 
      float rpm = -(avgPPS * 60.0) / PPR;
      avgVelocity = (rpm * CIRCUMFERENCE_MM) / 60.0; 
    } else {
      long deltaPos = currentPos - posHistory[0];
      if (historyIndex > 0) {
        float avgPPS = (float)deltaPos / historyIndex;
        float rpm = -(avgPPS * 60.0) / PPR;
        avgVelocity = (rpm * CIRCUMFERENCE_MM) / 60.0;
      }
    }
    historyIndex++;
    if (historyIndex >= WINDOW_SIZE) {
      historyIndex = 0;
      bufferFull = true;
    }
  }

  // Serial Monitor
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "avg") {
      // Changed here: Now it prints avgVelocity immediately, 
      // utilizing the running average calculated before the buffer fills.
      Serial.println((int)round(avgVelocity));
    }
  }
}

// ISR: Sustained Sampling Filter
void readEncoder() {
  // 1. Time-gate: Reject if too soon after last pulse
  unsigned long now = micros();
  if (now - lastPulseTime < DEBOUNCE_MICROS) return;

  // 2. Sustained Sampling: Pin A must be HIGH for 10 consecutive checks
  // This takes about 15-20 microseconds. 
  // High-frequency noise from the camera will flicker and fail this test.
  for(int i = 0; i < 10; i++) {
    if (digitalRead(pinA) == LOW) return; 
  }

  // 3. Direction Check with stability
  int b1 = digitalRead(pinB);
  delayMicroseconds(5); // Short delay to allow signal to stabilize
  int b2 = digitalRead(pinB);
  
  if (b1 == b2) {
    if (b1 == LOW) {
      encoderPosition++;
    } else {
      encoderPosition--;
    }
    lastPulseTime = now;
  }
}