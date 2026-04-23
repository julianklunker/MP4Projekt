import time
import tkinter as tk
import queue
from Camera.image_gen import update_image, update_cube
from Camera.Camera import Newteccam
from Converter import Converter
import cv2
import numpy as np
from robot.robotclasses import Maxi, bot1_dropoff_locations, bot2_dropoff_locations
from RobotGUI import start_gui
from data_anal import convert_to_hsv, find_objects, search_colors, find_contours

 

#starter cam, robot, converter og laver globalt billede (zeroes)
try:
    cam = Newteccam()
except:
    class Fake_cam:
        def __init__(self):
            self.HEIGHT = 1013
            self.WIDTH = 1296
    cam = Fake_cam()
    print(f"{__name__}\tFailed to connect to camera")

bots = {}

try:
    bots.update({"bot1": Maxi("/dev/ttyACM0")})
except:
    print(f"{__name__}\tFailed to connect to bot1")

try:
    bots.update({"bot2": Maxi("/dev/ttyACM1")})
except:
    print(f"{__name__}\tFailed to connect to bot2")

for bot_name, bot in bots.items():
    bot.set_speed(750)
    bot.move(x=0, y=0, z=200)

"""
try:
    bot1 = Maxi("/dev/ttyACM0")
except:
    print(f"{__name__}\tFailed to connect to bot1")
    bot1 = False
if bot1:
    print(f"{__name__}\tConnected to bot1")
    bot1.set_speed(750)
    bot1.move(x=0, y=0, z=200)

try:
    bot2 = Maxi("/dev/ttyACM1")
except:
    print(f"{__name__}\tFailed to connect to bot2")
    bot2 = False
if bot2:
    print(f"{__name__}\tConnected to bot2")
    bot2.set_speed(750)
    bot2.move(x=0, y=0, z=200)
"""

converter = Converter()
converter.calibrate(0,90,cam.WIDTH,-90)

motor_freq = 14
#belt_speed = 185 * motor_freq/50
belt_speed = 38

####Manlger at connect til belt arduino og få tal 
cube = np.zeros((cam.HEIGHT, cam.WIDTH, cam.HEIGHT), dtype=np.uint8)
image = np.zeros((cam.HEIGHT, cam.WIDTH,3), dtype=np.uint8)

frame_time = time.time()

data_queue = queue.Queue()
return_queue = queue.Queue()
start_gui(data_queue,return_queue)
data_queue.put({"belt_speed": belt_speed})

running = True
channel = 500

while running:
    while not return_queue.empty():
        msg = return_queue.get()
        print(f"{__name__}\t{msg}")
        if msg == "quit":
            print(f"{__name__}\t[Main] Stopping...")
            running = False
            break
        elif msg == "shift":
            channel += 10
            if channel > cam.HEIGHT:
                channel = 0

    if not running:
        break

    #Update image
    #line, cube = update_cube(cube, cam)
    line, image = update_image(image, cam)

    #image[:,:,0] = cube[:,:,channel]

    #Få belt speed

    #indputter zeroes og tilføjer en linje (kanal 500) til image og opdatere image konstant
    #line forbliver ændret 
    #line er hyperspektralt
    #image er kun fra en kanal

    #konvertere image til hsv  
    hsv_image = convert_to_hsv(image)

    #tager hsv_image, kører den igennem den kæde af funktioner i data_anal
    #Den tegner på hsv_image og returnere det sammen med en liste af objekter
    #objecter (farve, x-koordinat, tid)
    frame, new_objects = find_objects(image, hsv_image, greyscale_mode = False)

    #send frame til gui
    data_queue.put({"frame":   frame})

    #tilføjer nye objekter til den globale liste af objekter og printer dem
    if new_objects:
        data_queue.put({"objects": new_objects})
        for obj in new_objects:
            color = obj[0]
            for bot_name, bot in bots.items():
                if color in bot.dropoff_locs:
                    bot.objects.append(obj)
                    print(f"{__name__}\t[Router] {color} -> {bot_name}")
                else:
                    print(f"{__name__}\t[Router] {color} -> unknown, discarding")

    # tjekker om robotten er klar, hvis den er klar og der er objekter i køen
    # og den ikke allerede har et item, så tager den det første item i køen og 
    # sender det til robotten
    for bot_name, bot in bots.items():
        if bot.update():
            if bot.objects:
                print(f"{__name__}\tCurrent items for {bot_name}: {bot.objects}")
                item = bot.objects.pop(0) #(color, x-coord, time at camera)
                bot_x = round(converter.convert_x(item[1],2))
                time_at_bot = item[2] + converter.y_timing(belt_speed)[0]

                item = (item[0], bot_x, time_at_bot)
                print(f"{__name__}\tItem sent to {bot_name}:\n\t\t{item}")

                data_queue.put({f"ro{bot_name}_item": item})
                bot.pickcycle(item)



    """
    if bot1:
        if bot1.update():
            if bot1.objects:
                print(f"{__name__}\tCurrent items for bot1: {objects_bot1}")
                item = bot1.objects.pop(0)
                #item = objects_bot1.pop(0)
                #item = (farve, x-koordinat, tid)
                ##Tilføj om object er forbi robot
                bot_x = round(converter.convert_x(item[1]),2)
                time_at_bot = item[2] + converter.y_timing(belt_speed)[0]
                print(f"{__name__}\tTime diff: {time_at_bot - time.time()}")
                #if time_at_bot > time.time():
                if True:
                    item = (item[0], bot_x, time_at_bot)
                    print(f"{__name__}\tItem sent to bot1:\n\t\t{item}")

                    data_queue.put({"robot1_item": item})
                    bot1.pickcycle(item)
    if bot2: 
        if bot2.update():
            if bot2.objects:
                print(f"{__name__}\tCurrent items for bot2: {objects_bot2}")
                item = bot2.objects.pop(0)
                #item = objects_bot2.pop(0)
                #item = (farve, x-koordinat, tid)
                ##Tilføj om object er forbi robot
                bot_x = round(converter.convert_x(item[1]),2)
                time_at_bot = item[2] + converter.y_timing(belt_speed)[1]
                print(f"{__name__}\tTime diff: {time_at_bot - time.time()}")
                item = (item[0], bot_x, time_at_bot)
                print(f"{__name__}\tItem sent to bot2:\n\t\t{item}")

                data_queue.put({"robot2_item": item})
                bot2.pickcycle(item)
"""

for bot_name, bot in bots.items():
    bot.move(x=0,y=0,z=200)
    bot.close()

"""
if bot1:
    bot1.move(x=0,y=0,z=200)
    bot1.close()

if bot2:
    bot2.move(x=0,y=0,z=200)
    bot2.close()
"""



