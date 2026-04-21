"""
RobotGUI.py
-----------
Tkinter GUI that runs on its own thread.
Receives all data via a queue — never touched directly from other threads.

Data the queue accepts:
    {"frame":   np.ndarray}          — annotated BGR image to display
    {"objects": list}                — list of detected (color, x, time) tuples
    {"robot_item": tuple or None}    — what the robot is currently holding
    {"belt_speed": float}            — conveyor speed in mm/s
"""

import tkinter as tk
from turtle import right
from PIL import Image, ImageTk
import cv2
import queue
import threading


class RobotGUI:
    def __init__(self, root, data_queue: queue.Queue):
        self.root = root

        self.root.bind("<Escape>", self.key_handler)

        self.data_queue = data_queue
        self.current_frame = None

        self.root.title("Robot Control Dashboard")
        self.root.geometry("1000x600")
        self.root.configure(bg="#1e1e1e")

        self._build_layout()
        self.poll_queue()
        self.update_video_frame()

    def key_handler(self, event):
        self.data_queue.put("quit")

    def _build_layout(self):
        # ── Left: camera feed ────────────────────────────────────────────────
        left = tk.Frame(self.root, bg="#1e1e1e", width=1330, height=660)  # ← add fixed width
        left.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)  # ← fill=tk.Y not BOTH
        left.pack_propagate(False)  # ← add this, prevents children from resizing it

        tk.Label(left, text="Camera Feed", bg="#1e1e1e", fg="#aaaaaa",
             font=("Helvetica", 10)).pack(anchor="w")

        self.video_label = tk.Label(left, bg="black", width=1200, height=660)
        self.video_label.pack()

    # ── Right: info panels ───────────────────────────────────────────────
        right = tk.Frame(self.root, bg="#1e1e1e", width=300)
        right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)
        right.pack_propagate(False)

        # Robot1 status
        robot1_status_frame = tk.LabelFrame(right, text="Robot1", bg="#1e1e1e",
                                     fg="#aaaaaa", font=("Helvetica", 10))
        robot1_status_frame.pack(fill=tk.X, pady=(0, 10))

        self.robot_item_label = tk.Label(robot1_status_frame, text="Current item: None",
                                         bg="#1e1e1e", fg="white",
                                         font=("Helvetica", 11))
        self.robot_item_label.pack(pady=8, padx=8, anchor="w")

        # Robot2
        robot2_status_frame = tk.LabelFrame(right, text="Robot2", bg="#1e1e1e",
                                     fg="#aaaaaa", font=("Helvetica", 10))
        robot2_status_frame.pack(fill=tk.X, pady=(0, 10))

        self.robot2_item_label = tk.Label(robot2_status_frame, text="Current item: None",
                                          bg="#1e1e1e", fg="white",
                                          font=("Helvetica", 11))
        self.robot2_item_label.pack(pady=8, padx=8, anchor="w")

        # Belt speed
        belt_frame = tk.LabelFrame(right, text="Telemetry", bg="#1e1e1e",
                                   fg="#aaaaaa", font=("Helvetica", 10))
        belt_frame.pack(fill=tk.X, pady=(0, 10))

        self.belt_speed_label = tk.Label(belt_frame, text="Belt speed: — mm/s",
                                         bg="#1e1e1e", fg="white",
                                         font=("Helvetica", 11))
        self.belt_speed_label.pack(pady=8, padx=8, anchor="w")

        # Detected objects list
        obj_frame = tk.LabelFrame(right, text="Detected Objects", bg="#1e1e1e",
                                  fg="#aaaaaa", font=("Helvetica", 10))
        obj_frame.pack(fill=tk.BOTH, expand=True)

        self.objects_text = tk.Text(obj_frame, bg="#2d2d2d", fg="white",
                                    font=("Courier", 10), state=tk.DISABLED,
                                    relief=tk.FLAT, height=15)
        self.objects_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        

    # ── Queue polling — runs every 100ms ─────────────────────────────────────
    def poll_queue(self):
        while not self.data_queue.empty():
            data = self.data_queue.get()

            if "frame" in data:
                self.current_frame = data["frame"]

            if "objects" in data:
                self._update_objects_list(data["objects"])

            if "bot1 objects" in data:
                item1 = data["bot1 objects"]
                if item1:
                    color, robot_x, t = item1
                    text = f"Bot1 item: {color}  X={robot_x:.1f}mm"
                else:
                    text = "Bot1 item: None"
                self.robot1_item_label.config(text=text)

            if "bot2 objects" in data:
                item2 = data["bot2 objects"]
                if item2:
                    color, robot_x, t = item2
                    text = f"Bot2 item: {color}  X={robot_x:.1f}mm"
                else:
                    text = "Bot2 item: None"
                self.robot2_item_label.config(text=text)

            if "belt_speed" in data:
                self.belt_speed_label.config(
                    text=f"Belt speed: {data['belt_speed']:.0f} mm/s")

        self.root.after(100, self.poll_queue)

    # ── Video display — runs every 33ms (~30fps) ──────────────────────────────
    def update_video_frame(self):
        if self.current_frame is not None:
            frame = self.current_frame
            # Resize to fit the label area
            frame = cv2.resize(frame, (1330, 600))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk  # prevent garbage collection
            self.video_label.config(image=imgtk)

        self.root.after(33, self.update_video_frame)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _update_objects_list(self, objects):
        self.objects_text.config(state=tk.NORMAL)
        self.objects_text.delete("1.0", tk.END)
        if objects:
            for color, x, t in objects:
                self.objects_text.insert(tk.END, f"{color:8s} x={x:.0f}px\n")
        else:
            self.objects_text.insert(tk.END, "No objects detected")
        self.objects_text.config(state=tk.DISABLED)


def start_gui(data_queue: queue.Queue):
    """Call this from your main script to launch the GUI on its own thread."""
    def run():
        root = tk.Tk()
        app = RobotGUI(root, data_queue)
        root.mainloop()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread