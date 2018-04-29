# AutoWebCompat - Automatically detect web compatibility issues

[![Build Status](https://travis-ci.org/marco-c/autowebcompat.svg?branch=master)](https://travis-ci.org/marco-c/autowebcompat)

The aim of this project is creating a tool to automatically detect [web compatibility issues](https://wiki.mozilla.org/Compatibility#What_is_Web_Compatibility) without human intervention.


### Collecting screenshots

The project uses Selenium to collect web page screenshots automatically on Firefox and Chrome.

The crawler loads web pages from the URLs on the [webcompat.com tracker](https://webcompat.com/) and tries to reproduce the reported issues by interacting with the elements of the page. As soon as the page is loaded and after every interaction with the elements, the crawler takes a screenshot.

The crawler repeats the same steps in Firefox and Chrome, generating a set of comparable screenshots.

The `data/` directory contains the screenshots generated by the crawler (N.B.: This directory is not present in the repository itself, but it will be created automatically after you setup the project as described in the **Setup** paragraph).

### Labeling

Now that the screenshots are available, they need to be labeled. The labeling phase operates on couples of comparable screenshots.

There are three possible labels:
1. **Y** for couples of images that are clearly compatible;
2. **D** for couples of images that are compatible, but with content differences (e.g. on a news site, two screenshots could be compatible even though they are showing two different news, simply because the news shown depends on the time the screenshot was taken and not on the fact that the browser is different);
3. **N** for couples of images which are not compatible.

Here are some examples of the three labels:

**Y**
<img src="https://user-images.githubusercontent.com/1616846/35619755-4a932132-067f-11e8-8b1c-c2f70a6819f4.png" width=158 /> <img src="https://user-images.githubusercontent.com/1616846/35619749-458ac7b2-067f-11e8-868d-ac6e186dec98.png" width=158 />

**D**
<img src="https://user-images.githubusercontent.com/1616846/35619779-5d39f90a-067f-11e8-9e31-7c793c79f246.png" width=158 /> <img src="https://user-images.githubusercontent.com/1616846/35619800-6f25ff2e-067f-11e8-8792-f1c3d9c875d1.png" width=158 />

**N**
<img src="https://user-images.githubusercontent.com/1616846/35619822-7f65ed22-067f-11e8-9b2b-ea99cfd6f7de.png" width=158 /> <img src="https://user-images.githubusercontent.com/1616846/35619769-5724cafe-067f-11e8-8e6a-00d527ab3581.png" width=158 />

In the training phase, the best case is that we are able to detect between Y+D and N. If we are not able to do that, we should at least aim for the relaxed problem of detecting between Y and D+N. This is why we have this three labeling system.

The labeling technical details are described [in this issue](https://github.com/marco-c/autowebcompat/issues/2).

The bounding-box labeling allows us to store the areas where the incompatibilities lie.

<img src="https://user-images.githubusercontent.com/18056781/39081659-fdd4655e-4562-11e8-86f9-a5fab28634bf.JPG" />

<img src="https://user-images.githubusercontent.com/18056781/39081665-10eda006-4563-11e8-9455-986b5a23934e.jpg" />

- Press 'y' to mark the images as compatible.
- Press 'Enter' to select the regions.
- Click 'T' on top left of boundary boxes to toggle between colors. Green corresponds to 'n', yellow corresponds to 'd'.
- Press 'Enter' to save changes. 

### Training

Now that we have a dataset with labels, we can train a neural network to automatically detect screenshots that are incompatible. We are currently using a [Siamese architecture](https://papers.nips.cc/paper/769-signature-verification-using-a-siamese-time-delay-neural-network.pdf) with different Convolutional Neural Networks, but are open to test other ideas.

We plan to employ three training methodologies:
1. Training from scratch on the entire training set;
2. Finetuning a network previously pretrained on ImageNet (or other datasets);
3. Finetuning a network previously pretrained in an unsupervised fashion.

For the unsupervised training, we are using a related problem for which we already have labels (detecting screenshots belonging to the same website). The pre-training can be helpful because we have plenty of data (as we don't need to manually label them) and we can fine-tune the network we pre-train for our problem of interest.


## Structure of the project

- The **autowebcompat/utils.py** module contains some utility functions;
- The **autowebcompat/network.py** module contains neural network definition, optimizers definition, along with the loss and accuracy;
- The **collect.py** script is the crawler that collects screenshots of web pages in different browsers;
- The **label.py** script is a utility that helps labelling couples of screenshots (are they the same in the two browsers or are there differences?);
- The **pretrain.py** script trains a neural network on the website screenshots for a slightly different problem (for which we know the solution), so that we can reuse the network weights for the training on the actual problem;
- The **train.py** script trains the neural network on the website screenshots to detect compat issues;
- The **data_inconsistencies.py** script checks the generated screenshots and takes note of any data inconsistency (e.g. screenshots that were taken in Firefox but not in Chrome).

## Setup

**Python 3** is required.

- Install [Git Large File Storage](https://git-lfs.github.com/), either manually or through a package like `git-lfs` if available on your system (in case of using [PackageCloud](https://github.com/git-lfs/git-lfs/blob/master/INSTALLING.md)).
- Clone the repository with submodules: `git lfs clone --recurse-submodules REPO_URL`
- Install the dependencies in requirements.txt: `pip install -r requirements.txt`.
- Install the dependencies in test-requirements.txt: `pip install -r test-requirements.txt`.

## Training the network
- The **pretrain.py** or **train.py** script can be run to train the neural network, with the following options:

    ```
    -network                  To select which network architecture to use
                                                       
    -optimizer                To select the optimizer to use   
                              
    -classification_type      Either Y vs N + D or Y + N vs D

    --early_stoppping	      (Optional) To stop training when validation accuracy has stopped improving
    ```


## Communication

Real-time communication for this project happens on [Mozilla's IRC network](https://wiki.mozilla.org/IRC), irc.mozilla.org, in the #webcompat channel.
