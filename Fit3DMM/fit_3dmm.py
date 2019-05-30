import sys
import cv2
import numpy as np
import os.path as osp
import time
import dlib
from Fit3DMM.utils import crop_by_lm, crop_by_face_det
import logging

predictor_path = './Fit3DMM/shape_predictor_68_face_landmarks.dat'
model = './Fit3DMM/3dmm_cnn_resnet_101.caffemodel'
config = './Fit3DMM/deploy_network.prototxt'
trg_size = 224

net = cv2.dnn.readNet(model, config)
net.setInputsNames('data')
mean = np.load('./Fit3DMM/mean.npy')

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)


class NoInputFileError(Exception):
    pass


class NoDetectorError(Exception):
    pass


class NoFaceDetectedError(Exception):
    pass


def crop_image(img, use_landmark=True, detector=None, predictor=None):
    if detector is None:
        sys.exit('detector is None')
    img2 = cv2.copyMakeBorder(img, 0, 0, 0, 0, cv2.BORDER_REPLICATE)
    dets = detector(img, 1)
    print("> number of faces detected: {}".format(len(dets)))
    if len(dets) == 0:
        print("<crop_image> no detected face, exit")
        return None, None, None
    if len(dets) > 1:
        print("<crop_image> more than one face was detected, process only the first detected face")
    face = dets[0]
    # cv2.rectangle(img2, (face.left(), face.top()), (face.right(), face.bottom()), (0,0,255),2)

    if use_landmark:
        shape = predictor(img, face)
        nl = shape.num_parts
        landmarks = np.zeros((nl, 2), np.float32)
        for i in range(0, nl):
            landmarks[i, 0] = shape.part(i).x
            landmarks[i, 1] = shape.part(i).y
        img = crop_by_lm(img, shape, img2)
    else:
        landmarks = None
        img = crop_by_face_det(img, face, img2)

    img = cv2.resize(img, (trg_size, trg_size))
    return img, face, landmarks


def generate_3dmm_params(input_file, output_file, rotation=0):
    """
    :param input_file: image with human face
    :param output_file: bmf model params for the input human face
    :param rotation: 0 for no rotation, >0 for left direction, <0 for right direction
    :return: None
    """
    if not osp.isfile(input_file):
        raise NoInputFileError

    img = cv2.imread(input_file)
    if rotation > 0:
        img = cv2.transpose(img)
        img = cv2.flip(img, 1)
    elif rotation < 0:
        img = cv2.transpose(img)
        img = cv2.flip(img, 0)

    if detector is None and (img.shape != (trg_size, trg_size, 3)).any():
        raise NoDetectorError

    use_landmark = (predictor is not None)
    if detector is not None:
        img, _, _ = crop_image(img, use_landmark=use_landmark, detector=detector, predictor=predictor)

    if img is None:
        raise NoFaceDetectedError

    img2 = img.astype(np.float32) - mean
    net.setInput(cv2.dnn.blobFromImage(img2))
    # start_time = time.time()
    out = net.forward()
    # elapsed_time = time.time() - start_time
    # print('elapsed time is', elapsed_time)
    np.savetxt(output_file, out.transpose())