import serial
import time
import math
import re
import threading
from collections import deque

class VelocitySensor(threading.Thread):
    def __init__(self, port='COM12', baudrate=115200):
        # Initialize the Thread parent class
        super().__init__()
        
        # --- Configuration ---
        self.port = port
        self.baudrate = baudrate
        self.PPR = 2000.0
        self.RADIUS = 0.0275
        self.CIRCUMFERENCE_MM = 2.0 * math.pi * self.RADIUS * 1000.0
        
        # --- Threading Controls ---
        # daemon=True ensures this thread dies automatically if your main program crashes
        self.daemon = True 
        self._stop_event = threading.Event()
        self._data_lock = threading.Lock() # Prevents data corruption between threads
        
        # --- Data Storage ---
        self.velocity_history = deque(maxlen=256)
        self._current_velocity = 0.0
        self._avg_velocity = 0.0

        self.last_update = 0
        self.encoder_update_interval = 5
        
        # --- Connect to Serial ---
        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Give Arduino time to boot
            print(f"VelocitySensor: Connected to {self.port}")
        except serial.SerialException as e:
            print(f"VelocitySensor Error: Failed to connect on {self.port}. {e}")
            self.arduino = None

    def run(self):
        """This runs continuously in the background once you call sensor.start()"""
        if not self.arduino:
            return

        while not self._stop_event.is_set():
            try:
                self.arduino.write(b"avg\n")
                
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode('utf-8').strip()
                    
                    if response:
                        match = re.search(r'\d+', response)
                        if match:
                            delay_us = float(match.group())
                            vel = 0.00
                            
                            if delay_us > 0 and "Stopped" not in response:
                                pps = 1000000.0 / delay_us
                                vel = (pps / self.PPR) * self.CIRCUMFERENCE_MM
                                
                            self.velocity_history.append(vel)
                            
                            # Dynamic Moving Average Logic
                            window_size = 32 if vel < 90 else 128
                            actual_window = min(window_size, len(self.velocity_history))
                            
                            if actual_window > 0:
                                recent_values = list(self.velocity_history)[-actual_window:]
                                avg_vel = sum(recent_values) / actual_window
                            else:
                                avg_vel = 0.0

                            # Use the lock to safely update the variables
                            with self._data_lock:
                                self._current_velocity = vel
                                self._avg_velocity = avg_vel

                time.sleep(0.06) # Loop rate

            except serial.SerialException:
                print("VelocitySensor: Connection lost.")
                break

    # --- Methods for the Main Program to Call ---
    
    def get_data(self):
        """Returns a tuple of (current_velocity, average_velocity)"""
        with self._data_lock:
            self.last_update = time.time()
            return self._current_velocity, self._avg_velocity

    def stop(self):
        """Safely shuts down the background thread and closes the port"""
        self._stop_event.set()
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("VelocitySensor: Port closed.")
