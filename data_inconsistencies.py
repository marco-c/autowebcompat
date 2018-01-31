import os
import json
import csv


def get_inconsistencies():
    files = os.listdir('./data/')

    parsed = {}
    for file in files:
        parts = os.path.splitext(file)[0].split('_')
        
        ID = parts[0]
        if ID not in parsed:
            parsed[ID] = {}
        element = '_'.join(parts[1:-1])
        if element not in parsed[ID]:
            parsed[ID][element] = []
        parsed[ID][element].append(parts[-1])

    incons = []
    for key, value in parsed.items():
        for element, browsers in value.items():
            if len(browsers) < 2:
                incons.append([key, element, 'firefox' in browsers, 'chrome' in browsers])
    return incons


def main():
    print('[*] Getting inconsistencies in screenshots...')
    incons = get_inconsistencies()
    print('[*] {} inconsistencies found.'.format(len(incons)))

    print('[*] Writing to inconsistencies.csv... ', end='')
    with open('inconsistencies.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['WEBCOMPAT-ID', 'ELEMENT-ID', 'FIREFOX', 'CHROME'])
            for line in incons:
                writer.writerow(line)
    print('Done!')


if __name__=='__main__':
    main()
