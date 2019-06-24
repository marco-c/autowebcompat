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

labels = utils.read_labels()

utils.prepare_images()
all_image_names = [i for i in utils.get_images() if i in labels]
all_images = sum([[i + '_firefox.png', i + '_chrome.png'] for i in all_image_names], [])
image = utils.load_image(all_images[0])
input_shape = image.shape

def load_pair(fname):
    return [fname + '_firefox.png', fname + '_chrome.png']

def couples_generator(images):
    for i in images:
        yield load_pair(i), utils.to_categorical_label(labels[i], args.classification_type)

def gen_func(images, coupleIterator):
    index = 0
    for x_batch, y_batch in coupleIterator:
        yield images[index: index + BATCH_SIZE], x_batch, y_batch
        index += BATCH_SIZE

number_of_couples = sum(1 for e in couples_generator(all_image_names))

print(input_shape)

data_gen = utils.get_ImageDataGenerator(all_images, input_shape)
all_iterator = gen_func(all_image_names, utils.CouplesIterator(couples_generator(all_image_names), input_shape, data_gen, BATCH_SIZE))

model = load_model('best_pretrain_model.hdf5', custom_objects={'contrastive_loss': contrastive_loss})

images_for_analysis = []
for image_names, x_batch, y_batch in all_iterator:
    predictions = model.predict(x_batch)

    for batch_index in range(BATCH_SIZE):
        truth = y_batch[batch_index]
        prediction = np.round(predictions[batch_index])
        image_name = image_names[batch_index]

        if truth != np.round(prediction):
            images_for_analysis.append([ truth, prediction, image_name ])

# Create UI
window = tk.Tk()

image_view = tk.Frame(window)

image_view.pack(side="top")

panel1 = tk.Label(image_view)
panel1.grid(row=0, column=0)

panel1_text = tk.Label(image_view)
panel1_text.grid(row=1, column=0)

panel2 = tk.Label(image_view)
panel2.grid(row=0, column=1)

panel2_text = tk.Label(image_view)
panel2_text.grid(row=1, column=1)

prediction_text = tk.Label(image_view)
prediction_text.grid(row=2, column=0)

image_index = 0

# Fill with image
def show_next_image():
    global panel1, panel2, panel1_text, panel2_text, image_index

    if image_index >= len(images_for_analysis):
        image_index = len(images_for_analysis)

    truth, prediction, image_name = images_for_analysis[image_index]

    firefox_name =  image_name + "_firefox.png"
    chrome_name = image_name + "_chrome.png"

    img1 = ImageTk.PhotoImage(Image.open("data/" + firefox_name))
    panel1.configure(image=img1)
    panel1.image = img1
    panel1_text.config(text=firefox_name)

    img2 = ImageTk.PhotoImage(Image.open("data/" + chrome_name))
    panel2.configure(image=img2)
    panel2.image = img2
    panel2_text.config(text=chrome_name)

    prediction_text.config(text="Truth: {}, Prediction: {}".format(truth, prediction))

    image_index += 1

def show_prev_image():
    global image_index
    image_index -= 2
    if image_index < 0:
        image_index = 0

    show_next_image()

button_view = tk.Frame(image_view)
button_view.grid(row=2, column=1)

next_button = tk.Button(button_view, text="Next", command=show_next_image)
next_button.grid(row=0, column=1, ipadx=30, ipady=10, pady=20)

previous_button = tk.Button(button_view, text="Previous", command=show_prev_image)
previous_button.grid(row=0, column=0, ipadx=30, ipady=10, pady=20)

show_next_image()
window.bind('<Left>', lambda x: show_prev_image())
window.bind('<Right>', lambda x: show_next_image())

window.mainloop()
