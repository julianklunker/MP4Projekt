import cv2
import os
import queue
import numpy as np
import time 
import threading

#from sortingsystem.settings import config

class Camera(cv2.VideoCapture):
    """
    Base Class for all cameras.

    Inherits from cv2.VideoCapture and overwrites read method.
    """
    _auto_start_thread = True  # subclasses can set False to defer thread start

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = None
        self.processed_image = None
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._latest_frame = None
        self.height = None
        self.width = None
        self._capture_thread = None
        if self._auto_start_thread:
            self._start_capture_thread()

    def _start_capture_thread(self):
        # Read first frame here — after any subclass properties have been applied
        ret, img = cv2.VideoCapture.read(self)
        if ret:
            self._latest_frame = img
            self.height, self.width, *_ = img.shape
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def _capture_loop(self):
        """Background thread: continuously reads frames so the buffer stays drained."""
        while not self._stop_event.is_set():
            ret, frame = cv2.VideoCapture.read(self)
            if ret:
                with self.lock:
                    self._latest_frame = frame

    def read(self):
        """
        Returns the most recently captured frame.
        """
        with self.lock:
            if self._latest_frame is None:
                return None
            self.image = self._latest_frame.copy()
        return self.image

    def release(self):
        self._stop_event.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=2)
        super().release()

    def process(self, image):
        """
        Place-holder method.
        :param image:
        :return: a list of objects
        """
        self.processed_image = image
        return []

    def read_process(self):
        # with self.lock:
        return self.process(self.read())

    def get_images(self):
        # with self.lock:
        return self.image, self.processed_image


class Newteccam(Camera):
    _auto_start_thread = False  # thread starts after camera properties are set

    def __init__(self, settings, path='/dev/qtec/video0', API=cv2.CAP_V4L2, *args, **kwargs):
        self.WIDTH = settings["crops"][0][2] #n_pixels
        self.HEIGHT = settings["crops"][0][3] #n_channels
        self.fps = settings["framerate"]
        self.exposure = settings["controls"]["exposure_time_absolute"]["value"]

        super().__init__(path, API, *args, **kwargs)
        
        self.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
        self.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)
        self.set(cv2.CAP_PROP_FPS, self.fps)
        self.set(cv2.CAP_PROP_EXPOSURE, self.exposure)

        self._start_capture_thread()  # start only after all properties are applied

    def read(self):
        self.image = super().read()
        return self.image

    def process(self, image):
        objects, self.processed_image = self.model.process_image(image)
        return objects

#For testing
class Fake_cam:
    def __init__(self):
        self.HEIGHT = 600
        self.WIDTH = 1296
        self.blank = np.ones((self.HEIGHT,self.WIDTH,1),dtype=np.uint8)
        self.frame = 0
        self.pos = 50
        self.i = 0

    def read(self):
        fake_line = self.blank.copy()
        fake_line[:,self.pos:self.pos+50] * self.i
        self.i += 1
        if self.i == 1:
            self.i +=1
        if self.i > 8:
            self.i = 0
        self.frame +=1
        if self.frame % 75 == 0:
            self.pos += 75
            if self.pos > self.WIDTH - 75:
                self.pos = 50
        return fake_line 
