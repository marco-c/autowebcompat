import csv
import json
import os
import random
import threading

from PIL import Image
import keras
from keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
import numpy as np


def get_bugs():
    # TODO: Get data from webcompat using issue_parser (https://github.com/webcompat/issue_parser) if the file doesn't exist.
    with open('webcompatdata-bzlike.json', 'r') as f:
        return json.load(f)['bugs']


def mkdir(dir_name):
    try:
        os.mkdir(dir_name)
    except OSError:
        pass


def get_all_images():
    return [f for f in os.listdir('data/') if f.endswith('.png')]


def get_images():
    data = {
        'firefox': [],
        'chrome': [],
    }

    for file_name in get_all_images():
        assert 'firefox.png' in file_name or 'chrome.png' in file_name

        browser = 'firefox' if 'firefox.png' in file_name else 'chrome'

        data[browser].append(file_name[:file_name.index('_' + browser + '.png')])

    return [image for image in data['firefox'] if image in set(data['chrome'])]


def prepare_images():
    try:
        os.mkdir('data_resized')
    except OSError:
        pass

    for f in get_all_images():
        if os.path.exists(os.path.join('data_resized', f)):
            continue

        try:
            orig = Image.open(os.path.join('data', f))
            orig.load()
            channels = orig.split()
            if len(channels) == 4:
                img = Image.new('RGB', orig.size, (255, 255, 255))
                img.paste(orig, mask=channels[3])
            else:
                img = orig

            img = img.resize((192, 256), Image.LANCZOS)
            img.save(os.path.join('data_resized', f))
        except IOError as e:
            print(e)


images = {}


def load_image(fname, parent_dir='data_resized'):
    global images

    if fname in images:
        return images[fname]

    img = load_img(os.path.join(parent_dir, fname), target_size=(32, 24))
    x = img_to_array(img, data_format=keras.backend.image_data_format())

    images[fname] = x

    return x


def get_ImageDataGenerator(images, image_shape):
    data_gen = ImageDataGenerator(rescale=1. / 255)

    x = np.zeros((len(images),) + image_shape, dtype=keras.backend.floatx())

    for i, image in enumerate(images):
        x[i] = load_image(image)

    data_gen.fit(x)

    return data_gen


class CouplesIterator():
    def __init__(self, image_couples_generator, image_shape, image_data_generator, batch_size=32):
        self.image_couples_generator = image_couples_generator
        self.image_shape = image_shape
        self.image_data_generator = image_data_generator
        self.batch_size = batch_size
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        x_batch = [
            np.zeros((self.batch_size,) + self.image_shape, dtype=keras.backend.floatx()),
            np.zeros((self.batch_size,) + self.image_shape, dtype=keras.backend.floatx()),
        ]
        image_couples = [None] * self.batch_size
        y_batch = np.zeros(self.batch_size)

        with self.lock:
            for i in range(self.batch_size):
                image_couple, label = next(self.image_couples_generator)
                image_couples[i] = image_couple
                y_batch[i] = label

        for i, (i1, i2) in enumerate(image_couples):
            x1 = load_image(i1)
            x1 = self.image_data_generator.random_transform(x1.astype(keras.backend.floatx()))
            x1 = self.image_data_generator.standardize(x1)
            x2 = load_image(i2)
            x2 = self.image_data_generator.random_transform(x2.astype(keras.backend.floatx()))
            x2 = self.image_data_generator.standardize(x2)
            x_batch[0][i] = x1
            x_batch[1][i] = x2

        return x_batch, y_batch


def balance(it):
    # Initialise last_label to None so that cur_label != last_label
    # is always True for the first element in it.
    last_label = None

    queue = {
        0: [],
        1: []
    }

    for e in it:
        cur_label = e[1]

        if cur_label != last_label:
            # Maintain relative order.
            # Append element and pop from front.
            queue[cur_label].append(e)
            element = queue[cur_label].pop(0)
            last_label = cur_label
            yield element
        else:
            queue[cur_label].append(e)

    # After every element has been considered, some queue may still be
    # non-empty. If so, and provided the non-empty queue has label other
    # than last label, then take elements from there.
    other_label = 1 if last_label == 0 else 0
    while len(queue[other_label]) != 0:
        element = queue[other_label].pop(0)
        other_label = 1 if other_label == 0 else 0
        yield element


def make_infinite(gen_func, elems):
    while True:
        random.shuffle(elems)
        yield from gen_func(elems)


def read_labels(file_name='labels.csv'):
    try:
        with open(file_name, 'r') as f:
            next(f)
            reader = csv.reader(f)
            labels = {row[0]: row[1] for row in reader}
    except FileNotFoundError:
        labels = {}
    return labels


def to_categorical_label(label, classification_type='Y vs D + N'):
    if classification_type == 'Y vs D + N':
        if label == 'y':
            return 1
        else:
            return 0
    elif classification_type == 'Y + D vs N':
        if label == 'n':
            return 0
        else:
            return 1


def write_labels(labels, file_name='labels.csv'):
    with open(file_name, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Image Name', 'Label'])
        for key, values in labels.items():
            writer.writerow([key, values])
