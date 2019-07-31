# AutoWebCompat - Automatically detect web compatibility issues

[![Build Status](https://travis-ci.org/marco-c/autowebcompat.svg?branch=master)](https://travis-ci.org/marco-c/autowebcompat)

The aim of this project is creating a tool to automatically detect [web compatibility issues](https://wiki.mozilla.org/Compatibility#What_is_Web_Compatibility) without human intervention.


### Collecting screenshots

The project uses Selenium to collect web page screenshots automatically on Firefox and Chrome.

The crawler loads web pages from the URLs on the [webcompat.com tracker](https://webcompat.com/) and tries to reproduce the reported issues by interacting with the elements of the page. As soon as the page is loaded and after every interaction with the elements, the crawler takes a screenshot.

The crawler repeats the same steps in Firefox and Chrome, generating a set of comparable screenshots.

The `data/` directory contains the screenshots generated by the crawler (N.B.: This directory is not present in the repository itself, but it will be created automatically after you setup the project as described in the **Setup** paragraph).

### Labeling
[Labeling Guide](LABELING.md)

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
- Install all dependencies: `pip install pipenv && pipenv install --dev && pipenv shell`.

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
