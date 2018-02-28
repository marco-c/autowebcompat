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
    evaluate = K.eval(dist)
    dist2 = network.euclidean_distance([arr3, arr4])
    evaluate2 = K.eval(dist2)
    assert (evaluate == 1)
    assert (math.floor(evaluate2 * 100) == 360)


def test_eucl_distance_output_shape():
    vect = [arr1.shape, arr2.shape]
    shape = network.eucl_dist_output_shape(vect)
    assert (shape == (1, 1))


def test_contrastive_loss():
    label = [0, 1]  # possible values for output
    margin = 1
    loss_calculated = []
    close = []

    for a in label:
        euclid_dist = network.euclidean_distance([arr1, arr2])  # it returns 1
        loss1 = network.contrastive_loss(a, euclid_dist)
        eval1 = K.eval(loss1)
        loss = a * np.square(eval1) + (1 - a) * np.square(max(margin - eval1, 0))
        loss = np.mean(loss)
        loss_calculated.append(loss)
        close.append(math.isclose(loss, eval1))

    assert (close[0] != loss_calculated[0])  # 1 and 0 are not similar
    assert (close[1] == loss_calculated[1])
