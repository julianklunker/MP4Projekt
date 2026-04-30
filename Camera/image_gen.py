import cv2
import numpy as np
from time import time

whiteMatrix = np.load(r"AmsterDamModel/whiteMatrix.npy")
pca_mean = np.load(r"AmsterDamModel/pca_mean_10.npy")
pca_components = np.load(r"AmsterDamModel/pca_components_10.npy")
svm_model_coef = np.load(r"AmsterDamModel/svm_model_coef_10.npy")
svm_model_intercept = np.load(r"AmsterDamModel/svm_model_intercept_10.npy")
svm_classes = np.load(r"AmsterDamModel/svm_classes.npy")

label_to_color = {1:(0,0,0), # Background
                  2:(0,255,0),     #PA
                  3:(255,0,0),     #PC
                  4:(0,0,255),     #PE
                  5:(255,255,0),   #PET
                  6:(255,0,255),   #PLA
                  7:(0,255,255),   #PP
                  8:(255,255,255), #PS
                  0:(128,128,128)} #ABS

blank = np

def update_image(image, cam):
    line = cam.read() #(Channels, Pixels, 3)
    line = line[:,:,0].transpose() #(Pixels, Channels)
    #line = np.flip(line,axis=0).astype(np.uint8)

    line_white = line / whiteMatrix * 255

    line_pca = np.dot(line_white - pca_mean, pca_components.T)
    predictions = np.dot(line_pca, svm_model_coef.T) + svm_model_intercept
    encoded_predictions = np.argmax(predictions, axis=1)

    colored_line = np.zeros((encoded_predictions.shape[0], 3), dtype=np.uint8)

    for label, color in label_to_color.items():
        colored_line[encoded_predictions == label] = color

    image = np.roll(image,1,axis=0)
    image[0,:,:] = colored_line

    return (line, image)

def update_image_9(image, cam):
    line = cam.read() #(Channels, Pixels, 3)
    line = line[:,:,0].transpose() #(Pixels, Channels)
    #line = np.flip(line,axis=0).astype(np.uint8)

    line_white = line / whiteMatrix * 255

    line_pca = np.dot(line_white - pca_mean, pca_components.T)
    predictions = np.dot(line_pca, svm_model_coef.T) + svm_model_intercept
    encoded_predictions = np.argmax(predictions, axis=1)

    image = np.roll(image,1,axis=0)
    image[0,:,0] = encoded_predictions

    return image
