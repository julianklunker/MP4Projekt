import threading
import time
import tkinter as tk
import queue
from Camera.image_gen import update_image
from Camera.Camera import Newteccam
from Converter import Converter
import cv2
import numpy as np
from robot.robotclasses import Maxi

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
image = np.zeros((1096, 1340,3), dtype=np.uint8)

objects = []

frame_time = time.time()

mode = 0

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

    #tilføjer nye objekter til den globale liste af objekter og printer dem
    if new_objects:
        objects += new_objects
        print(f"Current objects:\n{objects}")


    #send info til gui

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
            bot.pickcycle(item)
            

    
