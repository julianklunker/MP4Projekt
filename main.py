import time
import cv2
import queue
import numpy as np
import tkinter as tk
 
from robot.robotclasses import Maxi
from robot.encoder import Encoder
from RobotGUI import start_gui
from data_anal import start_data_anal
#from data_anal import convert_to_hsv, find_objects, search_colors, find_contours
from Camera.image_gen import update_image, update_cube
from Camera.Camera import Newteccam, Fake_cam
from Converter import Converter
from items import items
from devices import find_com_ports

 

#starter cam, robot, converter og laver globalt billede (zeroes)
try:
    cam = Newteccam()
    #raise Exception
except Exception as err:
    cam = Fake_cam()
    print(f"{__name__}\tFailed to connect to camera")
    print(f"{__name__}\tError:\n{err}")

bots = {}
com_ports = find_com_ports()

try:
    bots.update({"bot1": Maxi(com_ports[0],list(items)[:int(len(items)/2)])})
except Exception as err:
    print(f"{__name__}\tFailed to connect to bot1")
    print(f"{__name__}\tError:\n{err}")

try:
    bots.update({"bot2": Maxi(com_ports[1],list(items)[int(len(items)/2):])})
except Exception as err:
    print(f"{__name__}\tFailed to connect to bot2")
    print(f"{__name__}\tError:\n{err}")

for bot_name, bot in bots.items():
    bot.set_speed(750)
    bot.move(x=0, y=0, z=200)

try:
    encoder = Encoder(com_ports[2])
except Exception as err:
    encoder = False
    print(f"{__name__}\tFailed to connect to encoder")
    print(f"{__name__}\tError:\n{err}")

belt_speed = 0

data_queue = queue.Queue()
return_queue = queue.Queue()
start_gui(data_queue,return_queue)
data_queue.put({"belt_speed": belt_speed})

converter = Converter()
converter.calibrate(0,90,cam.WIDTH,-90)

#cube = np.zeros((cam.HEIGHT, cam.WIDTH, cam.HEIGHT), dtype=np.uint8)
image = np.zeros((cam.HEIGHT, cam.WIDTH,3), dtype=np.uint8)

running = True
channel = 500
time_ = time.time()

print(f"{__name__}\tStarting main loop")
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

    if encoder:
        if time.time() > encoder.last_update + 30:
            encoder.get_speed()
            belt_speed = encoder.speed
            data_queue.put({"belt_speed": belt_speed})


    #Update image
    #line, cube = update_cube(cube, cam)
   # while time.time()-time_ < 0.01:
   #     time.sleep(0.005)

    line, image = update_image(image, cam, channel)
    start_data_anal(data_queue,return_queue,image)
    #fps = round(1/(time.time()-time_))
    time_ = time.time()
    #print(f"{__name__}\tFPS: {fps}")
    #image[:,:,0] = cube[:,:,channel]

    #Få belt speed

    #indputter zeroes og tilføjer en linje (kanal 500) til image og opdatere image konstant
    #line forbliver ændret 
    #line er hyperspektralt
    #image er kun fra en kanal

    #konvertere image til hsv  
    #hsv_image = convert_to_hsv(image)

    #tager hsv_image, kører den igennem den kæde af funktioner i data_anal
    #Den tegner på hsv_image og returnere det sammen med en liste af objekter
    #objecter (farve, x-koordinat, tid)
    #frame, new_objects = find_objects(image, hsv_image, greyscale_mode = False)

    #send frame til gui
    #data_queue.put({"frame":   frame})

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
                time_at_bot = item[2] + converter.y_timing(belt_speed)[0]

                item = (item[0], bot_x, time_at_bot)
                print(f"{__name__}\tItem sent to {bot_name}:\n\t\t{item}")

                data_queue.put({f"{bot_name} item": item})
                bot.pickcycle(item)

# End of loop
print(f"{__name__}\tClosing bots")
for bot_name, bot in bots.items():
    bot.move(x=0,y=0,z=200)
    bot.close()
    if not bot.is_open:
        print(f"{__name__}\tClosed {bot_name}")

