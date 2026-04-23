import cv2
from time import time
import random

color_library = {
    # Bot 1 colors
    "red":    ((0,   100, 100), (8,   255, 255), (0,   0,   255)),
    "green":  ((40,  100, 70),  (80,  255, 255), (0,   255, 0  )),
    "blue":   ((94,  80,  40),  (126, 255, 255), (255, 0,   0  )),
    "yellow": ((20,  80,  100), (40,  255, 255), (0,   255, 255)),
    "orange": ((10,  150, 130), (20,  255, 255), (0,   165, 255)),
    "pink":   ((160, 50,  100), (170, 255, 255), (203, 192, 255)),
    # Bot 2 colors
    "white":  ((0,   0,   200), (180, 15,  255), (255, 255, 255)),
    "purple": ((130, 50,  50),  (160, 255, 255), (128, 0,   128)),
    "cyan":   ((85,  100, 100), (95,  255, 255), (255, 255, 0  )),
    "brown":  ((10,  100, 40),  (20,  180, 125), (42,  42,  165)),
    "gray":   ((0,   0,   60),  (180, 25,  180), (128, 128, 128)),
    #"black":  ((0,   0,   1),   (180, 255, 40),  (50,  50,  50 )),
}

def convert_to_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

def find_objects(image, hsv_image, greyscale_mode=False):
    image = image.copy()
    hsv_image = hsv_image.copy()

    if greyscale_mode:
        # Use random color assignment for greyscale input
        mask = find_grey_objects(hsv_image)
        frame, objects = find_contours_grey(hsv_image, mask)
    else:
        # Normal color detection
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

assigned_colors = {}

def find_grey_objects(hsv_image):
    """Detect any grey/white/dark blobs — catches greyscale objects."""
    # Wide mask that catches anything not strongly saturated (greyscale)
    lower = (0,   0,  30)
    upper = (180, 50, 255)
    mask = cv2.inRange(hsv_image, lower, upper)
    mask = cv2.dilate(mask, None, iterations=1)
    return mask

def assign_random_color(cx):
    """Assign a random color from the library to an object, remembering it by x position."""
    if cx not in assigned_colors:
        assigned_colors[cx] = random.choice(list(color_library.keys()))
    return assigned_colors[cx]

def find_contours_grey(hsv_image, mask):
    """Like find_contours but assigns a random color to each detected object."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 800:
            x, y, w, h = cv2.boundingRect(cnt)
            cx = x + w // 2
            cy = y + h // 2

            # Assign a random color to this object
            color_name = assign_random_color(cx)
            _, _, draw_color = color_library[color_name]

            # Draw box and label
            cv2.rectangle(hsv_image, (x, y), (x + w, y + h), draw_color, 2)
            cv2.putText(hsv_image, color_name, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)
            cv2.circle(hsv_image, (cx, cy), 5, draw_color, -1)

            if y == 1:
                print(f"{color_name} object at: ({cx}, {cy})")
                objects.append((color_name, cx, time()))
                # Clean up memory once object is fully detected
                assigned_colors.pop(cx, None)

    return hsv_image, objects
