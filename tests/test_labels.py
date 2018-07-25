import os

from autowebcompat import utils


def _test_labels(labels):
    for label in labels:
        for browser in ['firefox', 'chrome']:
            assert os.path.join('data', '{}_{}.png'.format(label, browser))


def _test_validate_labels(labels):
    for label in labels.values():
        assert label in ['y', 'n', 'd']


def test_all_labels():
    labels = utils.read_labels()
    _test_labels(labels)
    _test_validate_labels(labels)

    labels_directory = 'label_persons'
    all_file_names = [f for f in os.listdir(labels_directory) if f.endswith('.csv')]
    for file_name in all_file_names:
        labels = utils.read_labels(os.path.join(labels_directory, file_name))
        _test_labels(labels)
        _test_validate_labels(labels)
