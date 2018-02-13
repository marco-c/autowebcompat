import json
import os
import threading
import numpy as np
from PIL import Image
import keras
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import csv


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
    return os.listdir('data/')


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


def load_image(fname):
    global images

    if fname in images:
        return images[fname]

    img = load_img(os.path.join('data_resized', fname), target_size=(32, 24))
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
    last_label = None
    queue_1 = []
    queue_0 = []
    for e in it:
        label = e[1]
        if label != last_label:
            last_label = label
            yield e
        else:
            if label == 1:
                queue_1.append(e)
            else:
                queue_0.append(e)

            while True:
                if last_label == 1:
                    if len(queue_0) == 0:
                        break
                    e = queue_0.pop()
                else:
                    if len(queue_1) == 0:
                        break
                    e = queue_1.pop()

                last_label = e[1]
                yield e


def read_labels(file_name='labels.csv'):
    try:
        with open(file_name, 'r') as f:
            next(f)
            reader = csv.reader(f)
            labels = {row[0]: row[1] for row in reader}
    except FileNotFoundError:
        labels = {}
    return labels


def write_labels(labels, file_name='labels.csv'):
    with open(file_name, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(["Image Name", "Label"])
        for key, values in labels.items():
            writer.writerow([key, values])
