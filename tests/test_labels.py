import os

import pytest

from autowebcompat import utils


def _test_labels(labels, data_dir):
    for label in labels:
        for browser in ['firefox', 'chrome']:
            assert os.path.exists(os.path.join(data_dir, '{}_{}.png'.format(label, browser)))


def _test_validate_labels(labels):
    for label in labels.values():
        assert label in ['y', 'n', 'd']


def test_example_labels():
    labels = utils.read_labels(os.path.join('testdata', 'labels.csv'))
    _test_labels(labels, 'testdata')
    _test_validate_labels(labels)


@pytest.mark.skipif(not os.path.isdir('data') or len(os.listdir('data')) == 0, reason='./data dir not available')
def test_all_labels():
    labels_directory = 'label_persons'
    all_file_names = [f for f in os.listdir(labels_directory) if f.endswith('.csv')]
    for file_name in all_file_names:
        labels = utils.read_labels(os.path.join(labels_directory, file_name))
        _test_labels(labels, 'data')
        _test_validate_labels(labels)
