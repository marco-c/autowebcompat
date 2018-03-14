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


def inconsistencies_metric(file_name):
    f = utils.get_all_images()
    total_img = len(f)
    with open(file_name, 'rU') as csvfile:
        reader = csv.DictReader(csvfile)
        data = {}
        for row in reader:
            for header, value in row.items():
                try:
                    data[header].append(value)
                except KeyError:
                    data[header] = [value]

    firefox = data['FIREFOX']
    n_incons = len(firefox)
    chrome = data['CHROME']
    incons_f = [int(x == "True") for x in firefox]
    incons_c = [int(x == "True") for x in chrome]
    print("Number of Photos: %d " % total_img)
    print("Number of Pair of images: %d " % int((total_img-n_incons)/2))
    print("Number of Pair of images possible: %d " % int((total_img-n_incons)/2 + n_incons))
    print("Percentage of Firefox Inconsistencies:%d  " % int(((n_incons-sum(incons_f))/n_incons)*100))
    print("Percentage of Chrome Inconsistencies:%d  "% int(((n_incons-sum(incons_c))/n_incons)*100))






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
    inconsistencies_metric('inconsistencies.csv')


if __name__ == '__main__':
    main()
