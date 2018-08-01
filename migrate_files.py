import os

from autowebcompat import utils

LATEST_VERSION = 2


def read_sequence(bug_id):
    with open('data/%d.txt' % bug_id) as f:
        return f.readlines()


def write_sequence(bug_id, data):
    with open('./data/%d.txt' % bug_id, 'w') as f:
        for i in range(len(data)):
            for j in range(i + 1):
                f.write(data[j])
            f.write('\n')


def migrate_v1_to_v2():
    all_data_files = os.listdir('data')
    label_files = os.listdir('label_persons')
    map_names = {}
    for i in range(7):
        map_names[i] = str(int((i + 1) * (i + 2) / 2 - 1))

    for f in all_data_files:
        if '.png' not in f:
            continue
        parts = f.split('_')

        if len(parts) <= 2:
            continue
        bug_id = parts[0]
        seq_no = int(parts[1])
        browser = parts[2]

        seq_no = map_names[seq_no]
        new_name = utils.create_file_name(bug_id=bug_id, browser=browser, seq_no=seq_no)
        os.rename(os.path.join('data', f), os.path.join('data', new_name))

    for f in all_data_files:
        if '.txt' not in f:
            continue
        bug_id = os.path.splitext(f)[0]
        data = read_sequence(int(bug_id))
        write_sequence(int(bug_id), data)

    for f in label_files:
        if 'csv' not in f:
            continue
        labels = utils.read_labels(os.path.join('label_persons', f))
        new_labels = {}

        for key, value in labels.items():
            key_info = utils.parse_file_name(key)

            if 'seq_no' not in key_info:
                new_labels[key] = value
                continue
            key = key.replace('_%d' % key_info['seq_no'], '_%s' % map_names[key_info['seq_no']])
            new_labels[key] = value
        utils.write_labels(new_labels, os.path.join('label_persons', f))

    for f in label_files:
        if 'json' not in f:
            continue

        bounding_boxes = utils.read_bounding_boxes(os.path.join('label_persons', f))
        new_bounding_boxes = {}

        for key, value in bounding_boxes.items():
            parts = key.split('_')

            if len(parts) <= 2:
                new_bounding_boxes[key] = value
                continue
            bug_id = parts[0]
            seq_no = int(parts[1])
            browser = parts[2]
            seq_no = map_names[seq_no]

            key = utils.create_file_name(bug_id=bug_id, browser=browser, seq_no=seq_no)
            new_bounding_boxes[key] = value
        utils.write_bounding_boxes(new_bounding_boxes, os.path.join('label_persons', f))


with open(os.path.join('data', 'VERSION'), 'r') as f:
    CURRENT_VERSION = int(f.read())

while CURRENT_VERSION != LATEST_VERSION:
    migrate_function = globals()['migrate_v%d_to_v%d' % (CURRENT_VERSION, CURRENT_VERSION + 1)]
    migrate_function()
    CURRENT_VERSION += 1

with open(os.path.join('data', 'VERSION'), 'w') as f:
    f.write(str(LATEST_VERSION))
