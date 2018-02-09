# AutoWebCompat - Automatically detect web compatibility issues

The aim of this project is creating a tool to automatically detect web compatibility issues without human intervention.

## Structure of the project

- The **collect.py** script collects screenshots of web pages in different browsers;
- The **label.py** script is a utility that helps labelling couples of screenshots (are they the same in the two browsers or are there differences?);
- The **utils.py** script contains some utility functions;
- The **network.py** script contains the neural network definition, along with the loss and accuracy;
- The **pretrain.py** script trains a neural network on the website screenshots for a slightly different problem (for which we know the solution), so that we can reuse the network weights for the training on the actual problem;
- The **train.py** script trains the neural network on the website screenshots to detect compat issues.

## Setup

**Python 3** is required.

- Install the dependencies in requirements.txt: `pip install -r requirements.txt`.
- Run the **get_dependencies.py** script.

## Communication

Real-time communication for this project happens on [Mozilla's IRC network](https://wiki.mozilla.org/IRC), irc.mozilla.org, in the #webcompat channel.
