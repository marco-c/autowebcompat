import argparse
import random
import time

from keras.callbacks import Callback
from keras.callbacks import EarlyStopping
from keras.callbacks import ModelCheckpoint

from autowebcompat import network
from autowebcompat import utils

BATCH_SIZE = 32
EPOCHS = 50
random.seed(42)

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--network', type=str, choices=network.SUPPORTED_NETWORKS, help='Select the network to use for training')
parser.add_argument('-o', '--optimizer', type=str, choices=network.SUPPORTED_OPTIMIZERS, help='Select the optimizer to use for training')
parser.add_argument('-w', '--weights', type=str, help='Location of the weights to be loaded for the given model')
parser.add_argument('-bw', '--builtin_weights', type=str, choices=network.SUPPORTED_WEIGHTS, help='Select the weights to be loaded for the given model')
parser.add_argument('-ct', '--classification_type', type=str, choices=utils.CLASSIFICATION_TYPES, default=utils.CLASSIFICATION_TYPES[0], help='Select the classification_type for training')
parser.add_argument('-es', '--early_stopping', dest='early_stopping', action='store_true', help='Stop training training when validation accuracy has stopped improving.')

args = parser.parse_args()


class Timer(Callback):
    def on_train_begin(self, logs={}):
        self.train_begin_time = time.time()
        self.epoch_times = []

    def on_epoch_begin(self, batch, logs={}):
        self.epoch_begin_time = time.time()

    def on_epoch_end(self, batch, logs={}):
        self.epoch_times.append(time.time() - self.epoch_begin_time)

    def on_train_end(self, logs={}):
        self.train_time = time.time() - self.train_begin_time


labels = utils.read_labels()

utils.prepare_images()
all_image_names = [i for i in utils.get_images() if i in labels]
all_images = sum([[i + '_firefox.png', i + '_chrome.png'] for i in all_image_names], [])
image = utils.load_image(all_images[0])
input_shape = image.shape

SAMPLE_SIZE = len(all_image_names)
TRAIN_SAMPLE = 80 * (SAMPLE_SIZE // 100)
VALIDATION_SAMPLE = 10 * (SAMPLE_SIZE // 100)
TEST_SAMPLE = SAMPLE_SIZE - (TRAIN_SAMPLE + VALIDATION_SAMPLE)


def load_pair(fname):
    return [fname + '_firefox.png', fname + '_chrome.png']


random.shuffle(all_image_names)
images_train, images_validation, images_test = all_image_names[:TRAIN_SAMPLE], all_image_names[TRAIN_SAMPLE:VALIDATION_SAMPLE + TRAIN_SAMPLE], all_image_names[SAMPLE_SIZE - TEST_SAMPLE:]


def couples_generator(images):
    for i in images:
        yield load_pair(i), utils.to_categorical_label(labels[i], args.classification_type)


def gen_func(images):
    return couples_generator(images)


train_couples_len = sum(1 for e in gen_func(images_train))
validation_couples_len = sum(1 for e in gen_func(images_validation))
test_couples_len = sum(1 for e in gen_func(images_test))

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
train_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_train), input_shape, data_gen, BATCH_SIZE)
validation_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_validation), input_shape, data_gen, BATCH_SIZE)
test_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, images_test), input_shape, data_gen, BATCH_SIZE)

model = network.create(input_shape, args.network, args.weights, args.builtin_weights)
network.compile(model, args.optimizer)

timer = Timer()
callbacks_list = [ModelCheckpoint('best_train_model.hdf5', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max'), timer]

if args.early_stopping:
    callbacks_list.append(EarlyStopping(monitor='val_accuracy', patience=2))

train_history = model.fit_generator(train_iterator, callbacks=callbacks_list, validation_data=validation_iterator, steps_per_epoch=train_couples_len / BATCH_SIZE, validation_steps=validation_couples_len / BATCH_SIZE, epochs=EPOCHS)
score = model.evaluate_generator(test_iterator, steps=test_couples_len / BATCH_SIZE)
print(score)

train_history = train_history.history
train_history.update({'epoch time': timer.epoch_times})
information = vars(args)
information.update({'Accuracy': score, 'Train Time': timer.train_time, 'Number of Train Samples': train_couples_len, 'Number of Validation Samples': validation_couples_len, 'Number of Test Samples': test_couples_len})
utils.write_train_info(information, model, train_history)
