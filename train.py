import json
import os
import numpy as np
import random
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.optimizers import SGD
from PIL import Image

import utils


with open('labels.json', 'r') as f:
    labels = json.load(f)


utils.prepare_images()


def load_image(fname):
    img = Image.open(os.path.join('data_resized', fname))
    # Numpy array x has format (height, width, channel)
    # or (channel, height, width)
    # but original PIL image has format (width, height, channel)
    data_format = keras.backend.image_data_format()
    x = np.asarray(img, dtype=keras.backend.floatx())
    if len(x.shape) == 3:
        if data_format == 'channels_first':
            x = x.transpose(2, 0, 1)
    elif len(x.shape) == 2:
        if data_format == 'channels_first':
            x = x.reshape((1, x.shape[0], x.shape[1]))
        else:
            x = x.reshape((x.shape[0], x.shape[1], 1))
    else:
        raise ValueError('Unsupported image shape: ', x.shape)
    return x


def load_pair(fname):
    f = load_image(fname + '_firefox.png')
    print(f.shape)
    c = load_image(fname + '_chrome.png')
    print(c.shape)
    return [f, c]


all_images = utils.get_images()
images_train = random.sample(all_images, len(all_images) - 10)
images_test = [i for i in all_images if i not in set(images_train)]
x_train = np.array([load_pair(i) for i in images_train])
y_train = keras.utils.to_categorical([random.randint(0,1) for image in images_train], num_classes=2)
x_test = np.array([load_pair(i) for i in images_test])
y_test = keras.utils.to_categorical([random.randint(0,1) for image in images_test], num_classes=2)

print(x_train.shape)
print(x_train[0].shape)
print(x_train[0][0].shape)
print(y_train.shape)
print(y_test.shape)
asd

model = Sequential()
# input: 192x256 images with 3 channels -> (192, 256, 3) tensors.
# this applies 32 convolution filters of size 3x3 each.
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(192, 256, 3)))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(2, activation='softmax'))

sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd)

model.fit(x_train, y_train, batch_size=32, epochs=10)
score = model.evaluate(x_test, y_test, batch_size=32)
