import csv
import os


def test_labels() :
    with open('../labels.csv') as csvfile:
        reader = csv.reader(csvfile,delimiter=',')
        for row in reader:
            if row[0] == 'Image Name' :
                continue
            file_name_firefox = '../data/'+ row[0] + '_' + 'firefox.png'
            file_name_chrome = '../data/'+ row[0] + '_' + 'chrome.png'
            assert os.path.exists(file_name_firefox)
            assert os.path.exists(file_name_chrome)
