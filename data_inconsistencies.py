import os
import csv


def get_inconsistencies():
    files = os.listdir('./data/')

    parsed = {}
    for file in files:
        parts = os.path.splitext(file)[0].split('_')

        ID = int(parts[0])
        if ID not in parsed:
            parsed[ID] = {}
        element = '_'.join(parts[1:-1])
        if element:
            spl = element.split('_')
            sequence = int(spl[-1])
            element = '_'.join(spl[:-1])
        else:
            element = None
            sequence = 0

        if (element, sequence) not in parsed[ID]:
            parsed[ID][(element, sequence)] = []
        parsed[ID][(element, sequence)].append(parts[-1])

    incons = []
    for key, value in parsed.items():
        for (element, sequence), browsers in value.items():
            if len(browsers) < 2:
                incons.append([key, element, sequence, 'firefox' in browsers, 'chrome' in browsers])

    incons.sort(key=lambda x: x[2])
    incons.sort(key=lambda x: x[0])
    return incons


def main():
    print('[*] Getting inconsistencies in screenshots...')
    incons = get_inconsistencies()
    print('[*] {} inconsistencies found.'.format(len(incons)))

    print('[*] Writing to inconsistencies.csv... ', end='')
    with open('inconsistencies.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['WEBCOMPAT-ID', 'ELEMENT-ID', 'SEQUENCE-NO', 'FIREFOX', 'CHROME'])
            for line in incons:
                writer.writerow(line)
    print('Done!')


if __name__ == '__main__':
    main()
