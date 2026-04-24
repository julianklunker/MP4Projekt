import cv2
import numpy as np
from time import time

def update_cube(cube, cam):
    print(f"{__name__}:{time()}\tReading")
    line = cam.read()
    line = line[:,:,0]
    print(f"{__name__}:{time()}\tRolling")
    cube = np.roll(cube,1,axis=0)
    cube[0,:,:] = line.transpose()
    print(f"{__name__}:{time()}\tReturning")
    return line, cube

def update_image(image, cam, channel):
    line = cam.read()
    line = line[:,:,0]
    image = np.roll(image,1,axis=0)
    #image[0,:,0] =line.transpose()[:,500]
    #print(image.shape)

    image[0,:505,0] = line.transpose()[:505,channel]
    image[0,505:,2] = line.transpose()[505:,channel]
    
    """
    image[0,:,0] =line.transpose()[:,400]
    image[0,:,1] =line.transpose()[:,500]
    image[0,:,2] =line.transpose()[:,700]
    """

    return (line, image)
