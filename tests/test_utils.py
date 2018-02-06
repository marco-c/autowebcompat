import sys
import os
sys.path.append(os.path.dirpath(os.path.realpath(__file__)) + '/../')

import utils  # noqa: E402


def test_get_bugs():
    bugs = utils.get_bugs()
    assert bugs


def test_get_all_images():
    images = utils.get_all_images()
    assert images
