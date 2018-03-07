import os
import csv
import re


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
            element = '_'.join(parts[1:-2])
        else:
            element = -1
            sequence = -1

        if (element, sequence) not in parsed[webcompatID]:
            parsed[webcompatID][(element, sequence)] = []
        parsed[webcompatID][(element, sequence)].append(parts[-1])

    incons = []
    for key, value in parsed.items():
        for (element, sequence), browsers in value.items():
            if element == -1:
                element = None
                if len(browsers) < 2:
                    incons.append([key, element, sequence, 'firefox' in browsers, 'chrome' in browsers])
            else :
                f = open("./data/" + str(key) + ".txt", 'r', encoding='utf-8')
                d = f.read().split('\n')
                l = []
                for i in d:
                    i = re.sub('[{}""]', '', i)
                    l.append(i[5:])
                element = l[sequence]
                if len(browsers) < 2:
                    incons.append([key, element, sequence, 'firefox' in browsers, 'chrome' in browsers])

    incons.sort(key=lambda x: (x[2], x[0]))
    return incons


def main():
    print('[*] Getting inconsistencies in screenshots...')
    incons = get_inconsistencies()
    print('[*] {} inconsistencies found.'.format(len(incons)))
    print('[*] Writing to inconsistencies.csv... ', end='')
    with open('inconsistencies.csv', 'w',encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['WEBCOMPAT-ID', 'ELEMENT-ID', 'SEQUENCE-NO', 'FIREFOX', 'CHROME'])
        for line in incons:
            writer.writerow(line)
    print('Done!')


if __name__ == '__main__':
    main()
