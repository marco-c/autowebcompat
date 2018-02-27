from autowebcompat import network
from autowebcompat import utils
from keras import backend as K
import numpy as np


a=np.random.rand(1,128)
b=np.random.rand(1,128)

def calc_dist(a,b):
    dist=np.sum(np.square(a-b))
    dist_sqroot=np.sqrt(max(dist,K.epsilon()))
    return dist_sqroot

def test_eucledian_distance():
    image0 = K.variable(value=a)
    image1 = K.variable(value=b)
    dist = network.euclidean_distance([image0,image1])
    evaluate=K.eval(dist)
    assert(evaluate==calc_dist(a,b))

def test_eucl_distance_output_shape():
    vect=[a.shape,b.shape]
    shape=network.eucl_dist_output_shape(vect)
    assert(shape==(1,1))


def test_contrastive_loss():
    euclid_dist=calc_dist(a,b)
    loss=network.contrastive_loss(euclid_dist,1)
    assert(loss>0)

