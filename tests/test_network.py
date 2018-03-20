import math

from keras import backend as K
import numpy as np

from autowebcompat import network

arr1 = np.array([[1, 1]], dtype=np.float32)
arr2 = np.array([[0, 1]], dtype=np.float32)

arr3 = np.array([[0, 0, 2], [2, 0, 1], [3, 1, 4]], dtype=np.float32)
arr4 = np.array([[3, 2, 2], [4, 3, 3], [4, 4, 2]], dtype=np.float32)

y_pred = np.array([0, 0.4, 0.7, 0.6, 0.5])
y_true = np.array([0, 1, 0, 0, 1])


def test_eucledian_distance():
    dist = network.euclidean_distance([arr1, arr2])
    assert(K.eval(dist) == 1)


def test_eucl_distance_output_shape():
    assert(network.eucl_dist_output_shape([arr1.shape, arr2.shape]) == (1, 1))
    assert(network.eucl_dist_output_shape([arr3.shape, arr4.shape]) == (3, 1))


def test_contrastive_loss():
    assert(K.eval(network.contrastive_loss(0, 1)) == 0)  # since the output and the label are far away
    assert(K.eval(network.contrastive_loss(1, 1)) == 1)  # since the output and the label are close
    assert(math.floor(K.eval(network.contrastive_loss(y_true, y_pred)) * 100) == 33)


def test_accuracy():
    assert(math.floor(K.eval(network.accuracy(y_true, y_pred)) * 100) == 60)
