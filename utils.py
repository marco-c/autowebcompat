import os
import numpy as np
from PIL import Image
import keras
from keras.preprocessing.image import Iterator


def get_all_images():
    return os.listdir('data/')


def get_images():
    data = {
        'firefox': [],
        'chrome': [],
    }

    for file_name in os.listdir('data/'):
        assert 'firefox.png' in file_name or 'chrome.png' in file_name

        browser = 'firefox' if 'firefox.png' in file_name else 'chrome'

        data[browser].append(file_name[:file_name.index('_' + browser + '.png')])

    return [image for image in data['firefox'] if image in set(data['chrome'])]


def prepare_images():
    try:
        os.mkdir('data_resized')
    except:
        pass

    for f in os.listdir('data/'):
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

    images[fname] = x

    return x


class CouplesIterator(Iterator):
    def __init__(self, image_couples, labels, image_data_generator, batch_size=32, shuffle=False, seed=None):
        self.image_couples = image_couples
        image = load_image(self.image_couples[0][0])
        self.labels = labels
        self.image_shape = image.shape
        self.image_data_generator = image_data_generator
        super(CouplesIterator, self).__init__(len(image_couples), batch_size, shuffle, seed)

    def next(self):
        # Keeps under lock only the mechanism which advances
        # the indexing of each batch.
        with self.lock:
            index_array, current_index, current_batch_size = next(self.index_generator)

        x_batch = [
            np.zeros((current_batch_size,) + self.image_shape, dtype=keras.backend.floatx()),
            np.zeros((current_batch_size,) + self.image_shape, dtype=keras.backend.floatx()),
        ]

        for i, j in enumerate(index_array):
            i1, i2 = self.image_couples[j]

            x1 = load_image(i1)
            x1 = self.image_data_generator.random_transform(x1)
            x1 = self.image_data_generator.standardize(x1)
            x2 = load_image(i2)
            x2 = self.image_data_generator.random_transform(x2)
            x2 = self.image_data_generator.standardize(x2)
            x_batch[0][i] = x1
            x_batch[1][i] = x2

        y_batch = self.labels[index_array]

        return x_batch, y_batch
