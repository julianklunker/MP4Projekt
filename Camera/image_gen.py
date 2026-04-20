import cv2
import numpy as np
from time import time

from Camera.Camera import Newteccam
from robot.robotclasses import Maxi
from Converter import Converter



def update_image(image, cam):
    line = cam.read()
    line = line[:,:,0]
    image = np.roll(image,1,axis=0)
    #image[0,:] =line.transpose()[:,500]
    #print(image.shape)
    image[0,:,0] =line.transpose()[:,500]

    return (line, image)