import os

from PIL import Image
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import img_to_array
import numpy as np
import pytest

from autowebcompat import utils


def test_get_bugs():
    bugs_file_path = os.path.join('testdata', 'webcompatdata-bzlike.json')
    bugs = utils.get_bugs(bugs_file_path)
    assert(isinstance(bugs, list))


def test_mkdir(tmpdir):
    direc_path = tmpdir.strpath + '/test'
    utils.mkdir(direc_path)
    assert(os.path.isdir(direc_path))
    utils.mkdir(direc_path)


def test_load_image(tmpdir):
    file_path = tmpdir.join('Image.jpg')
    img = Image.new('RGB', (30, 30))
    img.save(file_path.strpath)
    img = utils.load_image('Image.jpg', file_path.dirname)
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
    labels_path = os.path.join('testdata', 'labels.csv')
    labels = utils.read_labels(file_name=labels_path)
    assert(isinstance(labels, dict))


def test_write_labels(tmpdir):
    label = {'1': '1', '2': '2'}
    file_path = tmpdir.join('test.csv')
    utils.write_labels(label, file_name=file_path)
    assert(os.path.exists(file_path))
    assert(label == utils.read_labels(file_name=file_path))


def test_get_ImageDataGenerator(tmpdir):
    file_path = tmpdir.join('Image2.jpg')
    img = Image.new('RGB', (30, 30), color=(255, 0, 0))
    img.save(file_path.strpath)

    data_gen = utils.get_ImageDataGenerator(['Image2.jpg'], (32, 24, 3), file_path.dirname)
    assert(isinstance(data_gen, ImageDataGenerator))

    x = img_to_array(img, data_format=keras.backend.image_data_format())
    x = x.reshape((1,) + x.shape)
    X_batch = data_gen.flow(x).next()
    assert X_batch.shape[0] == x.shape[0]
    assert X_batch.shape[1:] == x.shape[1:]
    assert (X_batch >= 0).all() and (X_batch <= 1).all()


test_balance_data = [
    ('data1', 1),
    ('data2', 1),
    ('data3', 0),
    ('data4', 0),
    ('data5', 0),
    ('data6', 1)
]


@pytest.mark.parametrize('unbalanced_data', [
    test_balance_data,
    iter(test_balance_data)
])
def test_balance(unbalanced_data):
    balanced_data = utils.balance(unbalanced_data)

    assert(('data1', 1) == next(balanced_data))
    assert(('data3', 0) == next(balanced_data))
    assert(('data2', 1) == next(balanced_data))
    assert(('data4', 0) == next(balanced_data))
    assert(('data6', 1) == next(balanced_data))
    assert(('data5', 0) == next(balanced_data))

    with pytest.raises(StopIteration):
        next(balanced_data)


def test_balance_unbalanced_data():
    unbalanced_tuples = [
        ('data1', 1),
        ('data2', 1),
        ('data3', 1),
        ('data4', 0),
        ('data5', 0)]

    balanced_data = utils.balance(unbalanced_tuples)

    assert(('data1', 1) == next(balanced_data))
    assert(('data4', 0) == next(balanced_data))
    assert(('data2', 1) == next(balanced_data))
    assert(('data5', 0) == next(balanced_data))
    assert(('data3', 1) == next(balanced_data))

    with pytest.raises(StopIteration):
        next(balanced_data)


def test_to_categorical_label():
    label = 'y'
    categorical_label = utils.to_categorical_label(label, 'Y vs D + N')
    assert categorical_label == 1
    label = 'd'
    categorical_label = utils.to_categorical_label(label, 'Y vs D + N')
    assert categorical_label == 0
    label = 'n'
    categorical_label = utils.to_categorical_label(label, 'Y + D vs N')
    assert categorical_label == 0
    label = 'y'
    categorical_label = utils.to_categorical_label(label, 'Y + D vs N')
    assert categorical_label == 1


def test_create_file_name():
    assert(utils.create_file_name(bug_id='1661', browser='chrome', seq_no=None) == '1661_chrome')
    assert(utils.create_file_name(bug_id='1661', browser='chrome', width='20', height='10', seq_no=None) == '1661_H_20_V_10_chrome')
    assert(utils.create_file_name(bug_id='1661', browser='chrome', width='20', height='10', seq_no='2') == '1661_2_H_20_V_10_chrome')


def test_parse_file_name():
    info = {
        'bug_id': 1661
    }
    assert info == utils.parse_file_name('1661')

    info = {
        'bug_id': 1661,
        'seq_no': 2
    }
    assert info == utils.parse_file_name('1661_2')

    info = {
        'bug_id': 1661,
        'width': 20,
        'height': 10
    }
    assert info == utils.parse_file_name('1661_H_20_V_10')

    info = {
        'bug_id': 1661,
        'seq_no': 2,
        'width': 20,
        'height': 10
    }
    assert info == utils.parse_file_name('1661_2_H_20_V_10')
