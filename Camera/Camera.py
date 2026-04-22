import cv2
import os
import numpy as np
#from sortingsystem.settings import config
#from Models.KMeans_model.Color_detection import Color_detection
#from Models.Thresholdmodel.thresholdmodel import ThresholdModel
#from Models.Flensburgmodel.Flensburgmodel import Flensburgmodel
#from Models.Hamburgmodel.Hamburgmodel import Hamburgmodel
#from Models.Frankfurtmodel.Frankfurtmodel import Frankfurtmodel
#from Models.Dortmundmodel.Dortmundmodel import Dortmundmodel
#from Models.Dusseldorfmodel.Dusseldorfmodel import Dusseldorfmodel
#from Models.Kolnmodel.Kolnmodel import Kolnmodel
#from Object.Object import Object
import time 
import threading
#import json

#from sortingsystem.settings import config

class Camera(cv2.VideoCapture):
    """
    Base Class for all cameras.

    Inherits from cv2.VideoCapture and overwrites read method.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = None
        self.processed_image = None
        self.lock = threading.Lock()
        _, img = super().read()
        self.height, self.width, *_ = img.shape

    def read(self):
        """
        Overwrite read method.
        Returns frame
        """
        ret, self.image = super().read()
        if not ret:
            print(f"{__name__}\tNo frame recieved from camera. Trying again...")
            start_time = time.time()
            timeout = 30  # 30 seconds

            while time.time() - start_time < timeout:
                ret, self.image = super().read()
                if ret:
                    break
            else:
                print(f"{__name__}\tTimeout reached. Could not read from camera. Exiting...")
                exit()
        return self.image

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
    def __init__(self, path='/dev/qtec/video0', API=cv2.CAP_V4L2, *args, **kwargs):
        super().__init__(path, API, *args, **kwargs)
        self.HEIGHT = 1013
        self.WIDTH = 1340
        self.__CROP_TOP = 1096
        self.__CROP_LEFT = 1117

        self.fps = 30
        self.exposure = 5429

        self.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
        self.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)
        self.set(cv2.CAP_PROP_FPS, self.fps)
        self.set(cv2.CAP_PROP_EXPOSURE, self.exposure)

        os.system(f"v4l2-ctl -d {path} --set-crop top={self.__CROP_TOP},left={self.__CROP_LEFT},width={self.WIDTH},height={self.HEIGHT}")

    def read(self):
        self.image = super().read()
        return self.image

    def process(self, image):
        objects, self.processed_image = self.model.process_image(image)
        return objects
