import cv2
from time import time

color_library = {
    "red": ((0, 100, 100), (10, 255, 255), (0, 0, 255)),
    "green": ((40, 100, 70), (80, 255, 255), (0, 255, 0)),
    "blue": ((94, 80, 40), (126, 255, 255), (255, 0, 0)),
    "yellow": ((20, 80, 100), (40, 255, 255), (0, 255, 255)),
    "white": ((0, 0, 150), (180, 20, 255), (255, 255, 255)),
}

def convert_to_hsv(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

def find_objects(hsv_image):
    # 2. Loop through every color in our library
    hsv_image = hsv_image.copy()
    frame, objects = search_colors(hsv_image)

    return frame, objects


def search_colors(hsv_image):
    objects = []
    for color_name, (lower, upper, draw_color) in color_library.items():
        # Create a mask for THIS specific color
        mask = cv2.inRange(hsv_image, lower, upper)

        # Clean up the mask (remove speckles)
        mask = cv2.dilate(mask, None, iterations=1)

        # 3. Find the objects of this color

        frame, color_objects = find_contours(hsv_image, mask, color_name, draw_color)
        if color_objects:
            objects += color_objects
    return frame, objects


def find_contours(hsv_image, mask, color_name, draw_color):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 800: # Only track objects larger than 800 pixels
            x, y, w, h = cv2.boundingRect(cnt)

            # Draw the box and the name of the color found
            cv2.rectangle(hsv_image, (x, y), (x + w, y + h), draw_color, 2)
            cv2.putText(hsv_image, color_name, (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)

            #Find object centre
            cx = x + w // 2
            cy = y + h // 2
            cv2.circle(hsv_image, (cx, cy), 5, draw_color, -1)

            #Print the coordinates of the object centre once per second
            #print(f"{color_name} object at: ({cx}, {cy})")

            if y == 1:
                print(f"{color_name} object at: ({cx}, {cy})")
                objects.append((color_name,cx,time()))

    return hsv_image, objects