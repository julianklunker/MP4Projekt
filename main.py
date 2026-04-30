import time
import cv2
import queue
import os
import json
import numpy as np
import tkinter as tk
 
from robot.robotclasses import Maxi
from robot.encoder import Encoder
from RobotGUI import start_gui
from data_anal import convert_to_hsv, find_objects, search_colors, find_contours
from Camera.image_gen import update_image 
from Camera.Camera import Newteccam, Fake_cam
from Converter import Converter
from items import items
from devices import find_com_ports

 

#starter cam, robot, converter og laver globalt billede (zeroes)
os.system(r"quark-ctl config load --file '/home/root/MP4Projekt/AmsterDamConfig.json'")
with open("/home/root/MP4Projekt/AmsterDamModel/AmsterDamConfig.json") as f:
    settings = json.load(f)
try:
    cam = Newteccam(settings)
    #raise Exception
except Exception as err:
    cam = Fake_cam()
    print(f"{__name__}\tFailed to connect to camera")
    print(f"{__name__}\tError:\n{err}")

bots = {}
com_ports = find_com_ports()
print(com_ports)

try:
    bots.update({"bot1": Maxi(com_ports["bot1"], list(items)[:int(len(items)/2)], base_distance=577, pickup_ys=[-250, -150, -50, 50, 150, 250])})
except Exception as err:
    print(f"{__name__}\tFailed to connect to bot1")
    print(f"{__name__}\tError:\n{err}")

try:
    bots.update({"bot2": Maxi(com_ports["bot2"], list(items)[int(len(items)/2):], base_distance=988, pickup_ys=[-100, 0, 100])})
except Exception as err:
    print(f"{__name__}\tFailed to connect to bot2")
    if err:
        print(f"{__name__}\tError:\n{err}")
    else:
        print(f"{__name__}\tNo Error")

for bot_name, bot in bots.items():
    bot.set_speed(3000)
    bot.set_acceleration(40000)
    bot.move(x=0, y=0, z=50)

try:
    encoder = Encoder(com_ports["encoder"])
    belt_speed = 0
except Exception as err:
    encoder = False
    belt_speed = 50
    print(f"{__name__}\tFailed to connect to encoder")
    print(f"{__name__}\tError:\n{err}")

data_queue = queue.Queue()
return_queue = queue.Queue()
start_gui(data_queue,return_queue)
data_queue.put({"belt_speed": belt_speed})

converter = Converter()
converter.calibrate(0,125,cam.WIDTH,-105)

#image = np.zeros((cam.HEIGHT, cam.WIDTH,3), dtype=np.uint8)
image = np.zeros((cam.HEIGHT, cam.WIDTH), dtype=np.uint8)

running = True
time_ = time.time()

if encoder:
    encoder.last_update = 0  # trigger immediate first read
print(f"{__name__}\tStarting main loop")
i = 0
while running:
    new_objects = []
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
        elif type(msg) == list:
            print(f"{__name__}\t{msg}")
            new_objects += msg

    if not running:
        break

    #Få belt speed
    if encoder:
        if time.time() > encoder.last_update + encoder.encoder_update_interval:
            encoder.get_speed()
            belt_speed = encoder.speed
            data_queue.put({"belt_speed": belt_speed})

    #Update image
    #line, image = update_image(image, cam)
    image = update_image_9(image, cam)
    current_time = time.time()
    fps = round(1 / (current_time - time_)) if (current_time - time_) > 0 else 0
    time_ = current_time
    data_queue.put({"fps": fps})

    #objecter (farve, x-koordinat, tid)
    #frame, new_objects = find_objects(image)
    new_objects = find_materials(image)

    #send frame til gui
    data_queue.put({"frame": image})

    #tilføjer nye objekter til den globale liste af objekter og printer dem
    if new_objects:
        data_queue.put({"objects": new_objects})
        for obj in new_objects:
            color = obj[0]
            for bot_name, bot in bots.items():
                if color in bot.item_types:
                    bot.objects.append(obj)
                    print(f"{__name__}\t[Router] {color} -> {bot_name}")
                    break
                else:
                    print(f"{__name__}\t[Router] {color} -> unknown, discarding")

    # tjekker om robotten er klar, hvis den er klar og der er objekter i køen
    # sender det til robotten
    for bot_name, bot in bots.items():
        if bot.update():
            if bot.objects:
                print(f"{__name__}\tCurrent items for {bot_name}: {bot.objects}")
                item = bot.objects.pop(0) #(color, x-coord, time at camera)
                print(f"{__name__}\t{item}")
                bot_x = round(converter.convert_x(item[1]),2)

                item = (item[0], bot_x, item[2])  # (color, robot_x, original detection time)
                print(f"{__name__}\tItem sent to {bot_name}:\n\t\t{item}")

                data_queue.put({f"{bot_name} item": item})
                bot.pickcycle(item, belt_speed)

# End of loop
print(f"{__name__}\tClosing bots")
for bot_name, bot in bots.items():
    bot.home()
    bot.close()
    if not bot.is_open:
        print(f"{__name__}\tClosed {bot_name}")

