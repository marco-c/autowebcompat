from os import listdir

import utils


labels_directory = "label_persons/"
all_file_names = [f for f in listdir(labels_directory)]

labels_voted = {}
ydn_map = {'y': 0, 'd': 1, 'n': 2}
ydn_reverse_map = {0: 'y', 1: 'd', 2: 'n'}

for file_name in all_file_names:
    labels = utils.read_labels(labels_directory + file_name)
    for key, value in labels.items():
        if key not in labels_voted.keys():
            labels_voted[key] = [0, 0, 0]
        labels_voted[key][ydn_map[value]] += 1

labels = {}
for key, values in labels_voted.items():
    labels[key] = ydn_reverse_map[values.index(max(values))]

utils.write_labels(labels)
