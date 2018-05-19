from functools import lru_cache
from urllib.parse import urlparse
from keras.models import load_model
from autowebcompat.network import contrastive_loss
import itertools
import tkinter as tk
from PIL import ImageTk, Image
import numpy as np

from autowebcompat import utils

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

def couples_generator(images):
    for image_couple in itertools.combinations(images, 2):
        yield image_couple, 1 if are_same_site(image_couple[0], image_couple[1]) else 0


def gen_func(images):
    return utils.balance(couples_generator(images))


all_couples_len = sum(1 for e in gen_func(all_images))

print(input_shape)

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
all_iterator = utils.CouplesIterator(utils.make_infinite(gen_func, all_images), input_shape, data_gen, BATCH_SIZE)

model = load_model('pretrain.h5', custom_objects={'contrastive_loss': contrastive_loss})

predictions = model.predict_generator(all_iterator, steps=all_couples_len / BATCH_SIZE)

rounded_preds = np.round(predictions)

new_gen = utils.make_infinite(gen_func, all_images)
false_vals = []
for prediction in predictions:
    images, classid = next(new_gen)
    if classid != prediction:
        false_vals.append(images)

window = tk.Tk()

panel1 = tk.Label(window)
panel1.pack(side="left", padx=10)
panel2 = tk.Label(window)
panel2.pack(side="left", padx=10)

def show_next_image(image1, image2):
    img1 = ImageTk.PhotoImage(Image.open(image1))
    panel1.configure(image=img1)
    panel1.image = img1

    img2 = ImageTk.PhotoImage(Image.open(image2))
    panel2.configure(image=img2)
    panel2.image = img2



window.mainloop()