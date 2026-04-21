import cv2
import time
import queue
import tkinter as tk
import numpy as np

from Camera.image_gen import update_image
from Camera.Camera import Newteccam
from Converter import Converter
from robot.robotclasses import Maxi
from RobotGUI import start_gui

from data_anal import convert_to_hsv, find_objects, search_colors, find_contours

#starter cam, robot, converter og laver globalt billede (zeroes)
cam = Newteccam()
try:
    bot = Maxi("/dev/ttyACM0")
except:
    print("Failed to connect to bot")
    bot = False
if bot:
    bot.set_speed(750)
    bot.move(x=0,y=0)

converter = Converter()
converter.calibrate(0,90,1340,-90)

belt_speed = 200
####Manlger at connect til belt arduino og få tal 

image = np.zeros((cam.__HEIGHT, cam.WIDTH,3), dtype=np.uint8)

objects = []

frame_time = time.time()

data_queue = queue.Queue()
start_gui(data_queue)
data_queue.put({"belt_speed": belt_speed})

while True:
    """Få belt speed"""

    #indputter zeroes og tilføjer en linje (kanal 500) til image og opdatere image konstant
    #line forbliver ændret 
    line, image = update_image(image, cam)
    #line er hyperspektralt
    #image er kun fra en kanal



    #konvertere image til hsv  
    hsv_image = convert_to_hsv(image)

    #tager hsv_image, kører den igennem den kæde af funktioner i data_anal
    #Den tegner på hsv_image og returnere det sammen med en liste af objekter
    #objecter (farve, x-koordinat, tid)
    drawn_hsv_image, new_objects = find_objects(hsv_image)

    # Convert annotated image back to BGR for GUI
    drawn_bgr = cv2.cvtColor(drawn_hsv_image, cv2.COLOR_HSV2BGR)

    #tilføjer nye objekter til den globale liste af objekter og printer dem
    if new_objects:
        objects += new_objects
        print(f"Current objects:\n{objects}")


    #send info til gui
    data_queue.put({"frame":   drawn_bgr})
    data_queue.put({"objects": objects})

    # tjekker om robotten er klar, hvis den er klar og der er objekter i køen
    # og den ikke allerede har et item, så tager den det første item i køen og 
    # sender det til robotten
    if bot.update():
        if objects:
            print(objects)
            item = objects.pop(0)
            """item = (farve, x-koordinat, tid)"""
            ##Tilføj om object er forbi robot
            bot_x = round(converter.convert_x(item[1]),2)
            time_at_bot = item[2] + converter.y_timing(belt_speed)[0]
            item = (item[0], bot_x, time_at_bot)
            print(item)

            data_queue.put({"robot_item": item})
            bot.pickcycle(item)
            data_queue.put({"robot_item": None})

    
