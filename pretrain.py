import argparse
from functools import lru_cache
import itertools
import random
from urllib.parse import urlparse

from autowebcompat import network, utils

parser = argparse.ArgumentParser()
parser.add_argument('network', type=str, choices=network.SUPPORTED_NETWORKS, help='Select the network to use for training')
parser.add_argument('optimizer', type=str, choices=network.SUPPORTED_OPTIMIZERS, help='Select the optimizer to use for training')
args = parser.parse_args()

bugs = utils.get_bugs()

utils.prepare_images()
all_images = utils.get_all_images()[:3000]  # 3000
image = utils.load_image(all_images[0])
input_shape = image.shape
BATCH_SIZE = 32
EPOCHS = 50


bugs_to_website = {}
for bug in bugs:
    bugs_to_website[bug['id']] = urlparse(bug['url']).netloc


@lru_cache(maxsize=len(all_images))
def site_for_image(image):
    bug = image[:image.index('_')]
    return bugs_to_website[int(bug)]


def are_same_site(image1, image2):
    return site_for_image(image1) == site_for_image(image2)


images_train = random.sample(all_images, int(len(all_images) * 0.9))
images_test = [i for i in all_images if i not in set(images_train)]


def couples_generator(images):
    # for image_couple in itertools.combinations_with_replacement(images, 2):
    for image_couple in itertools.combinations(images, 2):
        yield image_couple, 1 if are_same_site(image_couple[0], image_couple[1]) else 0


def gen_func(images):
    return utils.balance(couples_generator(images))


train_couples_len = sum(1 for e in gen_func(images_train))
test_couples_len = sum(1 for e in gen_func(images_test))

print('Training with %d couples.' % train_couples_len)
print('Testing with %d couples.' % test_couples_len)
print(input_shape)

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
train_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_train), input_shape, data_gen, BATCH_SIZE)
test_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_test), input_shape, data_gen, BATCH_SIZE)

model = network.create(input_shape, args.network)
network.compile(model, args.optimizer)

model.save('pretrain.h5')

model.fit_generator(train_iterator, steps_per_epoch=train_couples_len / BATCH_SIZE, epochs=EPOCHS)

model.save('pretrain.h5')

score = model.evaluate_generator(test_iterator, steps=test_couples_len / BATCH_SIZE)
print(score)

asd = utils.CouplesIterator(utils.make_infinite(gen_func, images_test[:100]), input_shape, data_gen)
predict_couples_len = sum(1 for e in utils.balance(couples_generator(images_test)))
predictions = model.predict_generator(asd, steps=predict_couples_len / BATCH_SIZE)
print(predictions)
print([a[1] for a in utils.balance(couples_generator(images_test[:100]))])
