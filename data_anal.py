import cv2
import queue
import threading
from time import time, sleep
from items import items

color_library = {name: val["data"] for name, val in items.items()}

def convert_to_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

def find_objects(img):
    image = img.copy()
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    frame, objects = search_colors(image, hsv_image)

    return frame, objects


def search_colors(image, hsv_image):
    objects = []
    for color_name, (lower, upper, draw_color) in color_library.items():
        # Create a mask for THIS specific color
        mask = cv2.inRange(hsv_image, lower, upper)

        # Clean up the mask (remove speckles)
        mask = cv2.dilate(mask, None, iterations=1)

        # 3. Find the objects of this color

        frame, color_objects = find_contours(image, mask, color_name, draw_color)
        if color_objects:
            objects += color_objects
    return frame, objects


def find_contours(frame, mask, color_name, draw_color):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 800: # Only track objects larger than 800 pixels
            x, y, w, h = cv2.boundingRect(cnt)

            # Draw the box and the name of the color found
            cv2.rectangle(frame, (x, y), (x + w, y + h), draw_color, 2)
            cv2.putText(frame, color_name, (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)

            #Find object centre
            cx = x + w // 2
            cy = y + h // 2
            cv2.circle(frame, (cx, cy), 5, draw_color, -1)

            #Print the coordinates of the object centre once per second
            #print(f"{color_name} object at: ({cx}, {cy})")

            if y == 1:
                print(f"{__name__}\t{color_name} object at: ({cx}, {cy})")
                objects.append((color_name,cx,time()))

    return frame, objects

masks_index = [i for i in range(8)]

""" 
Jeg har ændret lidt i den men kunne ikk køre herhjemme endnu

def find_materials(img):
    masks = []
    for mask_i in masks_index:
        mask = image[img == mask_i]

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        objects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 800: # Only track objects larger than 800 pixels
                x, y, w, h = cv2.boundingRect(cnt)

                #Find object centre
                cx = x + w // 2
                cy = y + h // 2

                if y == 1:
                    print(f"{__name__}\tMaterial tag: {mask_i} object at: ({cx}, {cy})")
                    objects.append((mask_i,cx,time()))

    return frame, objects
"""
MATERIAL_COLORS = [
    (128, 128, 128),  # 0 — gray (background/empty)
    (0,   0,   255),  # 1 — red
    (255, 0,   0  ),  # 2 — blue
    (0,   255, 0  ),  # 3 — green
    (0,   255, 255),  # 4 — yellow
    (0,   165, 255),  # 5 — orange
    (203, 192, 255),  # 6 — pink
    (255, 255, 255),  # 7 — white
    (128, 0,   128),  # 8 — purple
    (255, 255, 0  ),  # 9 — cyan
]
 
MATERIAL_NAMES = [
    "empty", "red", "blue", "green", "yellow",
    "orange", "pink", "white", "purple", "cyan"
]
 
masks_index = list(range(1, 10))

def find_materials(img):
    h, w = img.shape[:2]
    frame = cv2.cvtColor(img * 25, cv2.COLOR_GRAY2BGR) 
 
    objects = []
    for mask_i in masks_index:
        binary_mask = (img == mask_i).astype("uint8") * 255
 
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
        color = MATERIAL_COLORS[mask_i]
        name  = MATERIAL_NAMES[mask_i]
 
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 800:  # only track objects larger than 800 pixels
                x, y, w_box, h_box = cv2.boundingRect(cnt)
 
                cv2.drawContours(frame, [cnt], -1, color, 2)
                cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), color, 1)
                cv2.putText(frame, name, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
 
                cx = x + w_box // 2
                cy = y + h_box // 2
                cv2.circle(frame, (cx, cy), 5, color, -1)
 
                if y == 1:
                    print(f"{__name__}\tMaterial {name} (tag={mask_i}) at: ({cx}, {cy})")
                    objects.append((name, cx, time()))
 
    return frame, objects
