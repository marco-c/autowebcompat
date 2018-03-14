import os
import csv
from autowebcompat import utils


def get_inconsistencies():
    files = os.listdir('./data/')

    parsed = {}
    for f in files:
        parts = os.path.splitext(f)[0].split('_')

        webcompatID = int(parts[0])
        if webcompatID not in parsed:
            parsed[webcompatID] = {}

        if len(parts) > 2:
            sequence = int(parts[-2])
        else:
            sequence = -1

        if sequence not in parsed[webcompatID]:
            parsed[webcompatID][sequence] = []
        parsed[webcompatID][sequence].append(parts[-1])

    incons = []
    for key, value in parsed.items():
        for sequence, browsers in value.items():
            if len(browsers) < 2:
                incons.append([key, sequence, 'firefox' in browsers, 'chrome' in browsers])

    incons.sort(key=lambda x: (x[2], x[0]))
    return incons


def print_statistics(file_name, incons):
    n_incons = len(incons)
    f = utils.get_all_images()
    total_img = len(f)
    firefox = []
    chrome = []
    for line in incons:
        firefox.append(line[2])
        chrome.append(line[3])

    incons_f = [int(x) for x in firefox]
    incons_c = [int(x) for x in chrome]
    print("Number of photos: {} " .format(total_img))
    print("Number of pairs of images: {} " .format(int((total_img - n_incons) / 2)))
    print("Number of pairs of images possible: {} " .format(int((total_img - n_incons) / 2 + n_incons)))
    print("Percentage of Firefox inconsistencies: {}  " .format(int(((n_incons - sum(incons_f)) / n_incons) * 100)))
    print("Percentage of Chrome inconsistencies: {} " .format(int(((n_incons - sum(incons_c)) / n_incons) * 100)))


def main():
    print('[*] Getting inconsistencies in screenshots...')
    incons = get_inconsistencies()
    print('[*] {} inconsistencies found.'.format(len(incons)))
    print('[*] Writing to inconsistencies.csv... ', end='')
    with open('inconsistencies.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['WEBCOMPAT-ID', 'SEQUENCE-NO', 'FIREFOX', 'CHROME'])
        for line in incons:
            writer.writerow(line)
    print('Done!')
    print_statistics('inconsistencies.csv', incons)


if __name__ == '__main__':
    main()
