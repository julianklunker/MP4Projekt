import serial
import time
#import threading
#import re
from items import items

#Settings
z_pickup = 0
z_move = 50
z_drop = 50
suck_pause_time = 2

class Robot(serial.Serial):
    """Base class for all robots."""
    def __init__(self, port, *args, **kwargs):
        super().__init__(port, baudrate=115200, timeout=10, *args, **kwargs)
        self.z_offset = 0
        self.home()

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
        print(f"{__name__}\tSending G-code: {gcode}")
        self.write(gcode)
    
    def pump_on(self):
        self.write("M03 D0")

    def pump_off(self):
        self.write("M05 D0")

    def pause(self, t: float):
        self.write(f"G04 P{t}")
    
    def home(self):
        self.write("G28")

class Maxi(Robot):
    MIN_LEAD_TIME = 0  # seconds of lead time needed before item arrives

    def __init__(self, port, item_types, base_distance, pickup_ys, *args, **kwargs):
        super().__init__(port, *args, **kwargs)

        self.z_offset = -825
        self.timenext = 0

        self.objects = []
        self.item_types = item_types
        self.base_distance = base_distance  # mm from camera to robot's y=0
        self.pickup_ys = sorted(pickup_ys)  # belt y-offsets, sorted closest first

    def pickcycle(self, item, belt_speed):
        color, x_coord, detected_time = item


        if color not in self.item_types:
            print(f"{__name__}\tError: No dropoff location for color '{color}'")
            return

        # Select the first pickup y-position the robot can still reach in time
        selected_y = None
        time_at_y = None
        now = time.time()
        for y in self.pickup_ys:
            if belt_speed <= 0:
                # avoid zero division and just pick the first position if belt isn't moving (whatever...)
                selected_y = self.pickup_ys[0]
                time_at_y = now + self.MIN_LEAD_TIME + 1
                break
            t = detected_time + (self.base_distance + y) / belt_speed
            if t > now + self.MIN_LEAD_TIME:
                selected_y = y
                time_at_y = t
                break

        if selected_y is None:
            print(f"{__name__}\tWARNING: Item '{color}' unreachable at all pickup positions — discarding")
            return

        print(f"{__name__}\tPickup y={selected_y}mm, arrives in {time_at_y - now:.2f}s")

        dropoff_x, dropoff_y = items[color]["drop_loc"]
        print(int(x_coord), int(selected_y), int(z_move))
        self.move(x=int(x_coord), y=int(selected_y), z=int(z_move))  # move to above the item, ready to pick
        wait_time = time_at_y - time.time()
        self.timenext = time.time() + wait_time + 1
        print(f"{__name__}\tRobot is waiting {wait_time*1000 - 20:.0f}ms")
        self.pause(wait_time * 1000 - 20)
        self.pump_on()
        self.pause(1)
        self.move(z=z_pickup)
        self.pause(suck_pause_time)
        self.move(z=z_move)

        self.move(x=dropoff_x, y=dropoff_y)
        #self.move(z=z_drop)

        self.pump_off()
        self.pause(suck_pause_time)  # Pause so vacuum is released
        #self.move(z=z_move)

    def update(self):
        if time.time() >= self.timenext:
            return True
        else:
            return False


