import json
import os
import numpy as np
import random
import keras
from keras.models import Sequential, Model
from keras.layers import Input, Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.optimizers import SGD
from keras.preprocessing.image import ImageDataGenerator
from PIL import Image
from urlparse import urlparse
import itertools

import utils


# TODO: Get data from webcompat using issue_parser if the file doesn't exist.
with open('issue_parser/webcompatdata-bzlike.json', 'r') as f:
    bugs = json.load(f)['bugs']


utils.prepare_images()


bugs_to_website = {}
for bug in bugs:
    bugs_to_website[bug['id']] = urlparse(bug['url']).netloc


def site_for_image(image):
    bug = image[:image.index('_')]
    return bugs_to_website[int(bug)]


def are_same_site(image1, image2):
    return site_for_image(image1) == site_for_image(image2)


all_images = utils.get_all_images()
'''images_train = random.sample(all_images, int(len(all_images) * 0.9))
images_test = [i for i in all_images if i not in set(images_train)]'''
print(len(all_images))
possible_combinations = list(itertools.combinations_with_replacement(all_images, 2))
print(len(possible_combinations))
images_train = random.sample(possible_combinations, len(possible_combinations) - 10)
labels_train = np.array([1 if are_same_site(i1, i2) else 0 for i1, i2 in images_train])
images_train_set = set(images_train)
images_test = [i for i in possible_combinations if i not in images_train_set]
labels_test = np.array([1 if are_same_site(i1, i2) else 0 for i1, i2 in images_test])

data_gen = ImageDataGenerator()
train_iterator = utils.CouplesIterator(images_train, labels_train, data_gen)
test_iterator = utils.CouplesIterator(images_test, labels_test, data_gen)

input_shape = (192, 256, 3)

network = Sequential()
# input: 192x256 images with 3 channels -> (192, 256, 3) tensors.
# this applies 32 convolution filters of size 3x3 each.
network.add(Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
network.add(Conv2D(32, (3, 3), activation='relu'))
network.add(MaxPooling2D(pool_size=(2, 2)))
network.add(Dropout(0.25))

network.add(Conv2D(64, (3, 3), activation='relu'))
network.add(Conv2D(64, (3, 3), activation='relu'))
network.add(MaxPooling2D(pool_size=(2, 2)))
network.add(Dropout(0.25))

network.add(Flatten())
network.add(Dense(256, activation='relu'))
network.add(Dropout(0.5))
network.add(Dense(2, activation='softmax'))


input_a = Input(shape=(192, 256, 3), batch_size=32)
input_b = Input(shape=(192, 256, 3), batch_size=32)
processed_a = network(input_a)
processed_b = network(input_b)

concatenated = keras.layers.concatenate([processed_a, processed_b])
out = Dense(1, activation='sigmoid')(concatenated)

model = Model([input_a, input_b], out)



sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])


model.fit_generator(train_iterator, steps_per_epoch=len(images_train) / 32, epochs=10)
score = model.evaluate_generator(test_iterator, steps=len(images_test))
