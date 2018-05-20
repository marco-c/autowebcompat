import argparse
from keras.models import load_model
from autowebcompat.network import contrastive_loss
import tkinter as tk
from PIL import ImageTk, Image
import numpy as np

from autowebcompat import utils

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--classification_type', type=str, choices=utils.CLASSIFICATION_TYPES, default=utils.CLASSIFICATION_TYPES[0], help='Select the classification_type for training')

args = parser.parse_args()

bugs = utils.get_bugs()

BATCH_SIZE = 32
EPOCHS = 50

labels = utils.read_labels()

utils.prepare_images()
all_image_names = [i for i in utils.get_images() if i in labels]
print(all_image_names)
all_images = sum([[i + '_firefox.png', i + '_chrome.png'] for i in all_image_names], [])
image = utils.load_image(all_images[0])
input_shape = image.shape

def load_pair(fname):
    return [fname + '_firefox.png', fname + '_chrome.png']

def couples_generator(images):
    for i in images:
        yield load_pair(i), utils.to_categorical_label(labels[i], args.classification_type)

def gen_func(images):
    return couples_generator(images)

number_of_couples = sum(1 for e in gen_func(all_image_names))

print(input_shape)

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
all_iterator = utils.CouplesIterator(gen_func(all_image_names), input_shape, data_gen, BATCH_SIZE)

model = load_model('best_train_model.hdf5', custom_objects={'contrastive_loss': contrastive_loss})

images_for_analysis = []
for x_batch, y_batch in all_iterator:
    predictions = model.predict(x_batch)

    for truth, prediction, image in zip(y_batch, predictions, x_batch):
        if truth != math.round(prediction):
            images_for_analysis.append([*x_batch, prediction])


# Create UI
window = tk.Tk()

image_view = tk.Frame(window)
image_view.pack()

panel1 = tk.Label(image_view)
panel1.grid(row=0, column=0)

panel1_text = tk.Label(image_view)
panel1_text.grid(row=1, column=0)

panel2 = tk.Label(image_view)
panel2.grid(row=0, column=1)

panel2_text = tk.Label(image_view)
panel2_text.grid(row=1, column=1)

prediction_text = tk.Label(image_view)
prediction_text.grid(row=2)

# Fill with image
def show_next_image():
    global panel1, panel2, panel1_text, panel2_text

    img1 = ImageTk.PhotoImage(Image.open("data/" + image1))
    panel1.configure(image=img1)
    panel1.image = img1
    panel1_text.config(text=image1)

    img2 = ImageTk.PhotoImage(Image.open("data/" + image2))
    panel2.configure(image=img2)
    panel2.image = img2
    panel2_text.config(text=image2)

    prediction_text.config("Prediction: " + str(prediction))

show_next_image(*false_vals[0])

next = tk.Button(window, text="Next")
next.pack(side="bottom", ipadx=30, ipady=30, pady=20)

window.mainloop()