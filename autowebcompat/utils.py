import csv
from datetime import datetime
import json
import os
import random
import subprocess
import sys
import threading

from PIL import Image
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import load_img
import numpy as np
from tensorflow.python.client import device_lib


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

            if img.size[1] > 732:
                img = img.crop((0, 0, img.size[0], 732))
            img = img.resize((192, 256), Image.LANCZOS)
            img.save(os.path.join('data_resized', f))
        except IOError as e:
            print(e)


images = {}


def load_image(fname, parent_dir='data_resized'):
    img = load_img(os.path.join(parent_dir, fname), target_size=(224, 224))
    return img_to_array(img, data_format=keras.backend.image_data_format())


def get_ImageDataGenerator(images, image_shape, parent_dir='data_resized'):
    data_gen = ImageDataGenerator(rescale=1. / 255)

    x = np.zeros((len(images),) + image_shape, dtype=keras.backend.floatx())

    for i, image in enumerate(images):
        x[i] = load_image(image, parent_dir)

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
    if os.stat(file_name).st_size == 0:
        raise Exception('labels file is empty')
    else:
        with open(file_name, 'r', newline='') as f:
            next(f)
            reader = csv.reader(f)
            labels = {row[0]: row[1] for row in reader}
    return labels


CLASSIFICATION_TYPES = ['Y vs D + N', 'Y + D vs N']


def to_categorical_label(label, classification_type):
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
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Image Name', 'Label'])
        for key, values in sorted(labels.items()):
            writer.writerow([key, values])


def read_bounding_boxes(file_name):
    try:
        with open(file_name, 'r') as f:
            bounding_boxes = json.load(f)
    except FileNotFoundError:
        bounding_boxes = {}
    return bounding_boxes


def write_bounding_boxes(bounding_boxes, file_name):
    with open(file_name, 'w') as f:
        print(json.dumps(bounding_boxes), file=f)


def get_all_model_summary(model, model_summary):
    line = []
    model.summary(print_fn=lambda x: line.append(x + '\n'))
    model_summary[model.get_config()['name']] = '\n' + ''.join(line)
    for layer in model.layers:
        if isinstance(layer, keras.engine.training.Model):
            get_all_model_summary(layer, model_summary)


def get_machine_info():
    parameter_value_map = {}
    operating_sys = sys.platform
    parameter_value_map['Operating System'] = operating_sys
    if 'linux' not in operating_sys:
        return parameter_value_map

    for i, device in enumerate(device_lib.list_local_devices()):
        if device.device_type != 'GPU':
            continue
        parameter_value_map['GPU_{}_name'.format(i + 1)] = device.name
        parameter_value_map['GPU_{}_memory_limit'.format(i + 1)] = device.memory_limit
        parameter_value_map['GPU_{}_description'.format(i + 1)] = device.physical_device_desc
    lscpu = subprocess.check_output('lscpu | grep \'^CPU(s):\|Core\|Thread\'', shell=True).strip().decode()
    lscpu = lscpu.split('\n')
    for row in lscpu:
        row = row.split(':')
        parameter_value_map[row[0]] = row[1].strip()
    return parameter_value_map


def write_train_info(information, model, train_history, file_name=None):
    if file_name is None:
        file_name = subprocess.check_output('uname -n', shell=True).strip().decode()
        file_name += datetime.now().strftime('_%H_%M_%Y_%m_%d.txt')
    machine_info = get_machine_info()
    information.update(machine_info)
    os.makedirs('train_info', exist_ok=True)
    with open(os.path.join('train_info', file_name), 'w') as f:
        for key, value in information.items():
            print('%s : %s' % (key, value), file=f)
        print('\n', file=f)
        model_summary = {}
        get_all_model_summary(model, model_summary)
        for key, value in model_summary.items():
            print('%s : %s' % (key, value), file=f)

        print('Sr.No.\t\t', end=' ', file=f)
        train_history_list = []
        for key, value in train_history.items():
            print('%s\t\t' % key, end=' ', file=f)
            train_history_list.append(value)
        train_history_list = np.transpose(np.array(train_history_list))
        for i in range(len(train_history_list)):
            print('\n%d\t\t' % (i + 1), end=' ', file=f)
            row = train_history_list[i]
            for col in row:
                print('%f\t\t' % col, end=' ', file=f)


def create_file_name(bug_id, browser, width=None, height=None, seq_no=None):
    new_file_name_parts = []
    new_file_name_parts.append(bug_id)

    if seq_no is not None:
        new_file_name_parts.append(seq_no)

    if width is not None:
        new_file_name_parts.append('H')
        new_file_name_parts.append(width)

    if height is not None:
        new_file_name_parts.append('V')
        new_file_name_parts.append(height)

    new_file_name_parts.append(browser)
    new_file_name = '_'.join(new_file_name_parts)
    return new_file_name


def parse_file_name(file_name):
    file_name_parts = file_name.split('_')
    file_info = {}
    file_info['bug_id'] = int(file_name_parts[0])

    shift = 0
    if len(file_name_parts) >= 2 and file_name_parts[1].isdigit():
        file_info['seq_no'] = int(file_name_parts[1])
        shift = 1
    if len(file_name_parts) > 2:
        file_info['width'] = int(file_name_parts[shift + 2])
        file_info['height'] = int(file_name_parts[shift + 4])
    return file_info
