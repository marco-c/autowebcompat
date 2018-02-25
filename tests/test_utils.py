import os
from tempfile import TemporaryDirectory
import numpy as np
from PIL import Image
from autowebcompat import utils


def test_get_bugs():
    bugs = utils.get_bugs()
    assert(isinstance(bugs, list))


def test_mkdir():
    d = TemporaryDirectory()
    direc_path = d.name + "/test"
    utils.mkdir(direc_path)
    assert(os.path.isdir(direc_path))
    utils.mkdir(direc_path)


def test_load_image(tmpdir):
    d = TemporaryDirectory()
    img = Image.new("RGB", (30, 30))
    img.save(d.name + "/Image.jpg")
    img = utils.load_image("Image.jpg", d.name)
    assert(isinstance(img, np.ndarray))
    assert(img.shape == (32, 24, 3))


def test_make_infinite():
    all_elems = list(range(7))

    inf_gen = utils.make_infinite(lambda elems: elems, all_elems)

    for _ in range(42):
        yielded = set()

        for i in all_elems:
            yielded.add(next(inf_gen))

        assert(yielded == set(all_elems))


def test_read_labels():
    labels = utils.read_labels(file_name='labels.csv')
    assert(isinstance(labels, dict))


def test_write_labels():
    label = {1: 1, 2: 2}
    d = TemporaryDirectory()
    file_path = d.name + "/test.csv"
    utils.write_labels(label, file_name=file_path)
    assert(os.path.exists(file_path))
