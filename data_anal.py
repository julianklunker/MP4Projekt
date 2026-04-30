import cv2
import queue
import threading
import numpy as np
from time import time, sleep
from items import items

# color_library = {name: val["data"] for name, val in items.items()}
#
# def convert_to_hsv(image):
#     return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#
# def find_objects(img):
#     image = img.copy()
#     hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#
#     frame, objects = search_colors(image, hsv_image)
#
#     return frame, objects
#
#
# def search_colors(image, hsv_image):
#     objects = []
#     for color_name, (lower, upper, draw_color) in color_library.items():
#         # Create a mask for THIS specific color
#         mask = cv2.inRange(hsv_image, lower, upper)
#
#         # Clean up the mask (remove speckles)
#         mask = cv2.dilate(mask, None, iterations=1)
#
#         # 3. Find the objects of this color
#
#         frame, color_objects = find_contours(image, mask, color_name, draw_color)
#         if color_objects:
#             objects += color_objects
#     return frame, objects
#
#
# def find_contours(frame, mask, color_name, draw_color):
#     contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     objects = []
#     for cnt in contours:
#         area = cv2.contourArea(cnt)
#         if area > 800: # Only track objects larger than 800 pixels
#             x, y, w, h = cv2.boundingRect(cnt)
#
#             # Draw the box and the name of the color found
#             cv2.rectangle(frame, (x, y), (x + w, y + h), draw_color, 2)
#             cv2.putText(frame, color_name, (x, y - 10),
#             cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)
#
#             #Find object centre
#             cx = x + w // 2
#             cy = y + h // 2
#             cv2.circle(frame, (cx, cy), 5, draw_color, -1)
#
#             #Print the coordinates of the object centre once per second
#             #print(f"{color_name} object at: ({cx}, {cy})")
#
#             if y == 1:
#                 print(f"{__name__}\t{color_name} object at: ({cx}, {cy})")
#                 objects.append((color_name,cx,time()))
#
#     return frame, objects

label_to_material = {"0":"ABS",
                     "2":"PA",
                     "3":"PC",
                     "4":"PE",
                     "5":"PET",
                     "6":"PLA",
                     "7":"PP",
                     "8":"PS"
                     }

masks_index = [0,2,3,4,5,6,7,8]
def find_materials(img):
    objects = []
    for mask_i in masks_index:
        mask = cv2.compare(img,mask_i,cv2.CMP_EQ)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 800: # Only track objects larger than 800 pixels
                x, y, w, h = cv2.boundingRect(cnt)

                #Find object centre
                cx = x + w // 2
                cy = y + h // 2

                if y == 1:
                    print(f"{__name__}\tMaterial tag: {mask_i} object at: ({cx}, {cy})")
                    objects.append((label_to_material[f"{mask_i}"],cx,time()))

    return objects
