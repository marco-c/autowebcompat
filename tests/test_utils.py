import os
import numpy as np
from tempfile import TemporaryDirectory
from autowebcompat import utils
from PIL import Image


def test_get_bugs():
    bugs = utils.get_bugs()
    assert(isinstance(bugs, list))


def test_mkdir():
    d = TemporaryDirectory()
    direc_path = os.path.join(d.name + "\\test")
    utils.mkdir(direc_path)
    assert(os.path.isdir(direc_path))
    utils.mkdir(direc_path)


def test_load_image():
    os.mkdir('data_resized')
    fake_img = np.random.rand(30, 30, 3) * 255
    img = Image.fromarray(fake_img.astype('uint8')).convert('RGBA')
    img.save("./data_resized/Image.jpg")
    img = utils.load_image("Image.jpg", "./data_resized")
    assert(isinstance(img, np.ndarray))
    os.remove("./data_resized/Image.jpg")
    os.rmdir("data_resized")


def test_read_labels():
    labels = utils.read_labels(file_name='labels.csv')
    assert(isinstance(labels, dict))


def test_write_labels():
    label = {1: 1, 2: 2}
    d = TemporaryDirectory()
    file_path = os.path.join(d.name + "\\test.csv")
    utils.write_labels(label, file_name=file_path)
    assert(os.path.exists(file_path))
