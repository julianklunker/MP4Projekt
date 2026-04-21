import serial
import time
import threading
import re

#Settings
z_pickup = 80
z_move = 120
z_drop = 80
suck_pause_time = 1

#Drop off locations
item_dropoff_locations = {
    "red":    (180, -170),
    "blue":   (180, -25),
    "green":  (180,  90),
    "yellow": (180, -130),
    "orange": (180, -80),
    "pink":   (180,  50),
    "white":   (-200, -25),
    "purple":  (-200, -170),
    "cyan":    (-200,  90),
    "brown":   (-200, -130),
    "gray":    (-200, -80),
    "black":   (-200,  50),
}

bot1_dropoff_locations = {
    "red":    (180, -170),
    "blue":   (180, -25),
    "green":  (180,  90),
    "yellow": (180, -130),
    "orange": (180, -80),
    "pink":   (180,  50),
}

bot2_dropoff_locations = {
    "white":   (-200, -25),
    "purple":  (-200, -170),
    "cyan":    (-200,  90),
    "brown":   (-200, -130),
    "gray":    (-200, -80),
    "black":   (-200,  50),
}


class Robot(serial.Serial):
    """Base class for all robots."""
    def __init__(self, port, *args, **kwargs):
        super().__init__(port, baudrate=115200, timeout=10, *args, **kwargs)
        self.z_offset = 0

    def write(self, gcode: str):
        super().write(f"{gcode} \n".encode())

    def set_speed(self, speed: int):
        self.move(F=speed)

    def set_acceleration(self, acceleration: int):
        self.move(A=acceleration)
    
    def move(self, **pos):
        gcode = "G01"
        for key, value in pos.items():
            key = key.upper()
            if key == "X":
                gcode += " X" + str(value)
            elif key == "Y":
                gcode += " Y" + str(value)
            elif key == "Z":
                gcode += " Z" + str(value + self.z_offset)
            elif key == "F":
                gcode += " F" + str(value)
            elif key == "A":
                gcode += " A" + str(value)
            elif key == "P":
                gcode = "G04 P" + str(value)
            elif key == "M":
                if len(str(value)) < 2:
                    gcode = "M" + "0" + str(value) + " D0"
                else:
                    gcode = "M" + str(value)
        self.write(gcode)
    
    def pump_on(self):
        self.write("M03 D0")

    def pump_off(self):
        self.write("M05 D0")

    def pause(self, t: float):
        self.write(f"G04 P{t}")

class Maxi(Robot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.z_offset = -825
        self.timenext = 0

    def pickcycle(self, item):
        color, x_coord, item_time = item  # unpack the tuple
        ###Tilføj time next
        self.timenext = time.time() + 1

        """item har (farve, x-koordinat, tid), den eneste jeg har brug for her er farve til sortering"""
        if color not in item_dropoff_locations:
            print(f"Error: No dropoff location for color '{color}'")
            return
    
        #dropoff_x, dropoff_y = item_dropoff_locations[color]
        dropoff_x, dropoff_y = item_dropoff_locations[color]

        self.move(x=x_coord, y=0)  
        self.pump_on()
        self.move(z=z_pickup)
        self.pause(suck_pause_time)
        self.move(z=z_move)

        self.move(x=dropoff_x, y=dropoff_y)
        self.move(z=z_drop)

        self.pump_off()
        self.pause(suck_pause_time)  # Pause so vacuum is released

    def update(self):
        if time.time() >= self.timenext:
            return True
        else:
            return False


