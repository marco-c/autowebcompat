import argparse
from functools import lru_cache
import itertools
import random
from urllib.parse import urlparse

from keras.callbacks import EarlyStopping, ModelCheckpoint

from autowebcompat import network, utils

SAMPLE_SIZE = 3000
BATCH_SIZE = 32
EPOCHS = 50
random.seed(42)

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--network', type=str, choices=network.SUPPORTED_NETWORKS, help='Select the network to use for training')
parser.add_argument('-o', '--optimizer', type=str, choices=network.SUPPORTED_OPTIMIZERS, help='Select the optimizer to use for training')
parser.add_argument('-es', '--early_stopping', dest='early_stopping', action='store_true', help='Stop training training when validation accuracy has stopped improving.')
args = parser.parse_args()

bugs = utils.get_bugs()

utils.prepare_images()
all_images = utils.get_all_images()[:SAMPLE_SIZE]
image = utils.load_image(all_images[0])
input_shape = image.shape

TRAIN_SAMPLE = 80 * (SAMPLE_SIZE // 100)
VALIDATION_SAMPLE = 10 * (SAMPLE_SIZE // 100)
TEST_SAMPLE = SAMPLE_SIZE - (TRAIN_SAMPLE + VALIDATION_SAMPLE)


bugs_to_website = {}
for bug in bugs:
    bugs_to_website[bug['id']] = urlparse(bug['url']).netloc


@lru_cache(maxsize=len(all_images))
def site_for_image(image):
    bug = image[:image.index('_')]
    return bugs_to_website[int(bug)]


def are_same_site(image1, image2):
    return site_for_image(image1) == site_for_image(image2)


random.shuffle(all_images)
images_train, images_validation, images_test = all_images[:TRAIN_SAMPLE], all_images[TRAIN_SAMPLE:VALIDATION_SAMPLE + TRAIN_SAMPLE], all_images[SAMPLE_SIZE - TEST_SAMPLE:]


def couples_generator(images):
    # for image_couple in itertools.combinations_with_replacement(images, 2):
    for image_couple in itertools.combinations(images, 2):
        yield image_couple, 1 if are_same_site(image_couple[0], image_couple[1]) else 0


def gen_func(images):
    return utils.balance(couples_generator(images))


train_couples_len = sum(1 for e in gen_func(images_train))
validation_couples_len = sum(1 for e in gen_func(images_validation))
test_couples_len = sum(1 for e in gen_func(images_test))

print('Training with %d couples.' % train_couples_len)
print('Validation with %d couples.' % validation_couples_len)
print('Testing with %d couples.' % test_couples_len)
print(input_shape)

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
train_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_train), input_shape, data_gen, BATCH_SIZE)
validation_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_validation), input_shape, data_gen, BATCH_SIZE)
test_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_test), input_shape, data_gen, BATCH_SIZE)

model = network.create(input_shape, args.network)
network.compile(model, args.optimizer)

callbacks_list = [ModelCheckpoint('best_pretrain_model.hdf5', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')]

if args.early_stopping:
    callbacks_list.append(EarlyStopping(monitor='val_accuracy', patience=2))

model.fit_generator(train_iterator, callbacks=callbacks_list, validation_data=validation_iterator, steps_per_epoch=train_couples_len / BATCH_SIZE, validation_steps=validation_couples_len / BATCH_SIZE, epochs=EPOCHS)

score = model.evaluate_generator(test_iterator, steps=test_couples_len / BATCH_SIZE)
print(score)

asd = utils.CouplesIterator(utils.make_infinite(gen_func, images_test[:100]), input_shape, data_gen)
predict_couples_len = sum(1 for e in utils.balance(couples_generator(images_test)))
predictions = model.predict_generator(asd, steps=predict_couples_len / BATCH_SIZE)
print(predictions)
print([a[1] for a in utils.balance(couples_generator(images_test[:100]))])
