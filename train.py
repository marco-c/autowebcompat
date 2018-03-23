import argparse
import random

from autowebcompat import network, utils

parser = argparse.ArgumentParser()
parser.add_argument('network', type=str, choices=network.SUPPORTED_NETWORKS, help='Select the network to use for training')
parser.add_argument('optimizer', type=str, choices=network.SUPPORTED_OPTIMIZERS, help='Select the optimizer to use for training')
args = parser.parse_args()

labels = utils.read_labels()

utils.prepare_images()
all_image_names = [i for i in utils.get_images() if i in labels]
all_images = sum([[i + '_firefox.png', i + '_chrome.png'] for i in all_image_names], [])
image = utils.load_image(all_images[0])
input_shape = image.shape
BATCH_SIZE = 32
EPOCHS = 50


def load_pair(fname):
    f = utils.load_image(fname + '_firefox.png')
    print(f.shape)
    c = utils.load_image(fname + '_chrome.png')
    print(c.shape)
    return [f, c]


images_train = random.sample(all_image_names, int(len(all_image_names) * 0.9))
images_test = [i for i in all_image_names if i not in set(images_train)]


def couples_generator(images):
    for i in images:
        yield load_pair(i), utils.to_categorical_label(labels[i], 'Y vs D + N')


def gen_func(images):
    return couples_generator(images)


train_couples_len = sum(1 for e in gen_func(images_train))
test_couples_len = sum(1 for e in gen_func(images_test))

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
train_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_train), input_shape, data_gen, BATCH_SIZE)
test_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_test), input_shape, data_gen, BATCH_SIZE)

model = network.create(input_shape, args.network)
network.compile(model, args.optimizer)

model.fit_generator(train_iterator, steps_per_epoch=train_couples_len / BATCH_SIZE, epochs=EPOCHS)
score = model.evaluate_generator(test_iterator, steps=test_couples_len / BATCH_SIZE)
print(score)
