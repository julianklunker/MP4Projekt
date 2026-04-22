import time
import tkinter as tk
import queue
from Camera.image_gen import update_image
from Camera.Camera import Newteccam
from Converter import Converter
import cv2
import numpy as np
from robot.robotclasses import Maxi, bot1_dropoff_locations, bot2_dropoff_locations
from RobotGUI import start_gui
from data_anal import convert_to_hsv, find_objects, search_colors, find_contours

TESTING = True
if TESTING:
    TEST_IMAGE = cv2.imread("all_colors_test.png")
    test_row = 0    

#starter cam, robot, converter og laver globalt billede (zeroes)
try:
    cam = Newteccam()
except:
    if TESTING:
        class Fake_cam:
            def __init__(self):
                self.HEIGHT = 1013
                self.WIDTH = 1340
        cam = Fake_cam()
    print(f"{__name__}\tFailed to connect to camera")

try:
    bot1 = Maxi("/dev/ttyACM0")
except:
    print(f"{__name__}\tFailed to connect to bot1")
    bot1 = False
if bot1:
    bot1.set_speed(750)
    bot1.move(x=0,y=0)

try:
    bot2 = Maxi("/dev/ttyACM2")
except:
    print(f"{__name__}\tFailed to connect to bot2")
    bot2 = False
if bot2:
    bot2.set_speed(750)
    bot2.move(x=0, y=0)

converter = Converter()
converter.calibrate(0,90,cam.WIDTH,-90)

belt_speed = 200
####Manlger at connect til belt arduino og få tal 
image = np.zeros((cam.HEIGHT, cam.WIDTH,3), dtype=np.uint8)

objects_bot1 = []
objects_bot2 = []

frame_time = time.time()

data_queue = queue.Queue()
start_gui(data_queue)
data_queue.put({"belt_speed": belt_speed})

running = True

while running:

    """
    while not data_queue.empty():
        msg = data_queue.get_nowait()
        if msg == "quit":
            print(f"{__name__}\t[Main] Stopping...")
            running = False
            break

    if not running:
        break
   """ 

    if TESTING:
        # Feed one row of the test image per loop iteration
        if test_row < TEST_IMAGE.shape[0]:
            image = np.roll(image, 1, axis=0)
            image[0] = TEST_IMAGE[test_row]
            test_row += 1
        else:
            print(f"{__name__}\t[Test] Image fully fed")
            break  # stop after full image is processed
    else:
        # Real camera
        line, image = update_image(image, cam)

    """Få belt speed"""

    #indputter zeroes og tilføjer en linje (kanal 500) til image og opdatere image konstant
    #line forbliver ændret 
    #line er hyperspektralt
    #image er kun fra en kanal

    #konvertere image til hsv  
    hsv_image = convert_to_hsv(image)

    #tager hsv_image, kører den igennem den kæde af funktioner i data_anal
    #Den tegner på hsv_image og returnere det sammen med en liste af objekter
    #objecter (farve, x-koordinat, tid)
    drawn_hsv_image, new_objects = find_objects(hsv_image, greyscale_mode = False)

    # Convert annotated image back to BGR for GUI
    drawn_bgr = cv2.cvtColor(drawn_hsv_image, cv2.COLOR_HSV2BGR)


    #send frame til gui
    data_queue.put({"frame":   drawn_bgr})

    #tilføjer nye objekter til den globale liste af objekter og printer dem
    if new_objects:
        for obj in new_objects:
            color = obj[0]
            if color in bot1_dropoff_locations:
                objects_bot1.append(obj)
                print(f"{__name__}\t[Router] {color} -> bot1")
            elif color in bot2_dropoff_locations:
                objects_bot2.append(obj)
                print(f"{__name__}\t[Router] {color} -> bot2")
            else:
                print(f"{__name__}\t[Router] {color} -> unknown, discarding")
        #send objects to GUI
        data_queue.put({"bot1 objects": objects_bot1})
        data_queue.put({"bot2 objects": objects_bot2})

    """
    if data_queue.qsize() > 1:
        print(f"{__name__}\tData queue:\n\t\t{data_queue.qsize()}")
    """


    # tjekker om robotten er klar, hvis den er klar og der er objekter i køen
    # og den ikke allerede har et item, så tager den det første item i køen og 
    # sender det til robotten
    if bot1:
        if bot1.update():
            if objects_bot1:
                print(f"{__name__}\tCurrent items for bot1: {objects_bot1}")
                item = objects_bot1.pop(0)
                """item = (farve, x-koordinat, tid)"""
                ##Tilføj om object er forbi robot
                bot_x = round(converter.convert_x(item[1]),2)
                time_at_bot = item[2] + converter.y_timing(belt_speed)[0]
                if time_at_bot > time.time():
                    item = (item[0], bot_x, time_at_bot)
                    print(f"{__name__}\tItem sent to bot1:\n\t\t{item}")

                    data_queue.put({"robot1_item": item})
                    bot1.pickcycle(item)
    if bot2: 
        if bot2.update():
            if objects_bot2:
                print(f"{__name__}\tCurrent items for bot2: {objects_bot2}")
                item = objects_bot2.pop(0)
                """item = (farve, x-koordinat, tid)"""
                ##Tilføj om object er forbi robot
                bot_x = round(converter.convert_x(item[1]),2)
                time_at_bot = item[2] + converter.y_timing(belt_speed)[1]
                item = (item[0], bot_x, time_at_bot)
                print(f"{__name__}\tItem sent to bot2:\n\t\t{item}")

                data_queue.put({"robot2_item": item})
                bot2.pickcycle(item)

if bot1:
    bot1.move(x=0,y=0,z=200)
    bot1.close()

if bot2:
    bot2.move(x=0,y=0,z=200)
    bot2.close()



