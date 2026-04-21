"""
pipeline_test.py
-----------------
Fully self-contained test — no camera, no serial port, no robot needed.

What it does:
1. Launches the GUI on a parallel thread
2. Generates a fake BGR image with colored blobs
3. Runs detection pipeline (convert_to_hsv → find_objects)
4. Converts pixel x → robot x using Converter
5. Passes items to FakeRobot — prints confirmations
6. Streams the annotated frame + all state into the GUI via queue

Run with:
    python pipeline_test.py
"""

import cv2
import numpy as np
import queue
import time as time_module
from time import time

from data_anal import convert_to_hsv, find_objects
from Converter import Converter
from RobotGUI import start_gui

# ── FakeRobot ─────────────────────────────────────────────────────────────────
item_dropoff_locations = {
    "red":    (180, -170),
    "blue":   (180, -25),
    "green":  (180,  90),
    "yellow": (-200, -170),
    "white":  (-200, -25),
}

class FakeRobot:
    def __init__(self):
        self.item = None
        print("[FakeRobot] Initialized — no serial port needed")

    def set_speed(self, speed):
        print(f"[FakeRobot] Speed set to {speed}")

    def pickup(self, item):
        self.item = item
        color, robot_x, t = item
        print(f"\n[FakeRobot] pickup() called")
        print(f"  Color    : {color}")
        print(f"  Robot X  : {robot_x:.2f} mm")
        print(f"  Timestamp: {t:.3f}")

    def pickcycle(self, item):
        color, robot_x, t = item
        print(f"\n[FakeRobot] pickcycle() called")
        print(f"  Color    : {color}")
        print(f"  Robot X  : {robot_x:.2f} mm")

        if color not in item_dropoff_locations:
            print(f"  ERROR — no dropoff location for '{color}'")
            return

        dropoff_x, dropoff_y = item_dropoff_locations[color]
        print(f"  Dropoff  : X={dropoff_x}, Y={dropoff_y}")
        print(f"  Robot would move to ({dropoff_x}, {dropoff_y}) and drop '{color}' item")
        self.item = None

    def update(self):
        return True


# ── Fake image builder ────────────────────────────────────────────────────────
BGR_COLORS = {
    "red":    (0,   0,   200),
    "green":  (0,   200, 0  ),
    "blue":   (200, 50,  50 ),
    "yellow": (0,   220, 220),
    "white":  (220, 220, 220),
}

def make_test_image(width=1340, height=100):
    image = np.zeros((height, width, 3), dtype=np.uint8)
    colors_to_place = list(BGR_COLORS.keys())
    n = len(colors_to_place)
    blob_w, blob_h = 80, 40

    for i, color_name in enumerate(colors_to_place):
        x_start = int((i / n) * width) + 50
        x_end   = x_start + blob_w
        y_start = 2   # offset by 1 to land at y=1 after dilation
        y_end   = y_start + blob_h
        image[y_start:y_end, x_start:x_end] = BGR_COLORS[color_name]
        print(f"[ImageGen] Placed {color_name:6s} blob at pixel x={x_start}-{x_end}")

    return image


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    IMAGE_WIDTH      = 1340
    belt_speed       = 200
    belt_travel_time = 1.5

    print("=" * 55)
    print("  PIPELINE TEST WITH GUI")
    print("=" * 55)

    # 1. Create shared queue and launch GUI on its own thread
    data_queue = queue.Queue()
    start_gui(data_queue)
    print("[Main] GUI launched on parallel thread")
    time_module.sleep(0.5)  # give tkinter a moment to initialize

    # 2. Setup converter and robot
    converter = Converter()
    converter.calibrate(pixel_x1=0, robot_x1=90, pixel_x2=IMAGE_WIDTH, robot_x2=-90)
    bot = FakeRobot()
    bot.set_speed(750)

    # Send initial belt speed to GUI
    data_queue.put({"belt_speed": belt_speed})

    # 3. Build fake image and run detection
    print("\n── Generating fake image and running detection ──")
    raw_image = make_test_image(width=IMAGE_WIDTH)
    hsv_image = convert_to_hsv(raw_image)
    drawn_hsv, detected_objects = find_objects(hsv_image)

    # Convert annotated HSV image back to BGR for the GUI
    drawn_bgr = cv2.cvtColor(drawn_hsv, cv2.COLOR_HSV2BGR)

    print(f"\n  Detected {len(detected_objects)} object(s):")
    for obj in detected_objects:
        print(f"    {obj}")

    # Send frame and object list to GUI
    data_queue.put({"frame":   drawn_bgr})
    data_queue.put({"objects": detected_objects})

    # 4. Robot loop
    print("\n── Sending objects to robot ──")
    objects = list(detected_objects)

    while objects or bot.item:
        if bot.update():
            if objects and not bot.item:
                raw_item = objects.pop(0)
                color, pixel_x, detected_time = raw_item

                robot_x       = round(converter.convert_x(pixel_x), 2)
                time_at_robot = detected_time + belt_travel_time
                bot_item      = (color, robot_x, time_at_robot)

                print(f"\n  Converted pixel {pixel_x} -> robot X {robot_x:.2f} mm")
                bot.pickup(bot_item)
                data_queue.put({"robot_item": bot.item})   # update GUI

            elif bot.item:
                bot.pickcycle(bot.item)
                data_queue.put({"robot_item": None})        # robot is free

        time_module.sleep(0.3)  # small pause so GUI updates are visible

    print("\nAll objects processed")
    print("[Main] GUI still running — close the window to exit\n")

    # Keep main thread alive so the daemon GUI thread isn't killed
    try:
        while True:
            time_module.sleep(1)
    except KeyboardInterrupt:
        print("\n[Main] Exiting")