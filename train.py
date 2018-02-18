import random

from autowebcompat import network
from autowebcompat import utils


labels = utils.read_labels()

utils.prepare_images()
all_images = utils.get_images()
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


images_train = random.sample(all_images, int(len(all_images) * 0.9))
images_test = [i for i in all_images if i not in set(images_train)]


def couples_generator(images):
    for i in images:
        yield load_pair(i), labels[i]


def inf_couples_generator(images):
    while True:
        for e in couples_generator(images):
            yield e


train_couples_len = sum(1 for e in couples_generator(images_train))
test_couples_len = sum(1 for e in couples_generator(images_test))

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
train_iterator = utils.CouplesIterator(inf_couples_generator(images_train), input_shape, data_gen, BATCH_SIZE)
test_iterator = utils.CouplesIterator(inf_couples_generator(images_test), input_shape, data_gen, BATCH_SIZE)

model = network.create(input_shape)
network.compile(model)

model.fit_generator(train_iterator, steps_per_epoch=train_couples_len / BATCH_SIZE, epochs=EPOCHS)
score = model.evaluate_generator(test_iterator, steps=test_couples_len / BATCH_SIZE)
print(score)
