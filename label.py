import os
import json
from PIL import ImageTk, Image
from tkinter import Tk, Label

import utils


try:
    with open('labels.json', 'r') as f:
        labels = json.load(f)
except:
    labels = {}


images_to_show = [i for i in utils.get_images() if i not in labels]
current_image = None

root = Tk()
panel1 = Label(root)
panel1.pack(side="left", padx=10)
panel2 = Label(root)
panel2.pack(side="left", padx=10)


def get_new_image():
    global current_image
    if len(images_to_show) == 0:
        root.quit()
        return
    current_image = images_to_show.pop()
    print("data/%s_firefox.png" % current_image)
    img = ImageTk.PhotoImage(Image.open("data/%s_firefox.png" % current_image))
    panel1.configure(image=img)
    panel1.image = img
    img = ImageTk.PhotoImage(Image.open("data/%s_chrome.png" % current_image))
    panel2.configure(image=img)
    panel2.image = img


# The images are the same.
def callback_y(e):
    labels[current_image] = 'y'
    get_new_image()


# The image are basically the same, except for advertisement or content.
def callback_d(e):
    labels[current_image] = 'd'
    get_new_image()


# The images are not the same.
def callback_n(e):
    labels[current_image] = 'n'
    get_new_image()


def callback_skip(e):
    get_new_image()


def close(e):
    root.quit()


get_new_image()
root.bind("y", callback_y)
root.bind("d", callback_d)
root.bind("n", callback_n)
root.bind("<Return>", callback_skip)
root.bind("<Escape>", close)
root.mainloop()


# Store results.
with open('labels.json', 'w') as f:
    json.dump(labels, f)
