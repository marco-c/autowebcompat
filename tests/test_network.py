from autowebcompat import network
from keras import backend as K
import math
import numpy as np

arr1 = np.array([[1, 1]], dtype=np.float32)
arr2 = np.array([[0, 1]], dtype=np.float32)

arr3 = np.array([[0, 0]], dtype=np.float32)
arr4 = np.array([[3, 2]], dtype=np.float32)


def test_eucledian_distance():
    dist = network.euclidean_distance([arr1, arr2])
    dist2 = network.euclidean_distance([arr3, arr4])
    assert (K.eval(dist) == 1)
    assert (math.floor(K.eval(dist2) * 100) == 360)


def test_eucl_distance_output_shape():
    vect = [arr1.shape, arr2.shape]
    assert (network.eucl_dist_output_shape(vect) == (1, 1))


def test_contrastive_loss():
    label = [0, 1]  # possible values for output
    euclid_dist = network.euclidean_distance([arr1, arr2])  # it returns 1
    loss1 = network.contrastive_loss(label[0], euclid_dist)
    loss2 = network.contrastive_loss(label[1], euclid_dist)
    assert (K.eval(loss1) == 0)  # since the output and the label are far away
    assert (K.eval(loss2) == 1)  # since the output and the label are close


def test_accuracy():
    y_pred = np.array([0, 0.4, 0.7, 0.6, 0.5])
    y_true = np.array([0, 1, 0, 0, 1])
    assert (math.floor(K.eval(network.accuracy(y_true, y_pred)) * 100) == 60)

