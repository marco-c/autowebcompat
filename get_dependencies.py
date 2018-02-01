import sys
import os
import tarfile
from zipfile import ZipFile
import requests


def download(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


print('[*] Extracting webdriver archives...')
for f in ['geckodriver', 'nightly', 'chromedriver', 'chrome-linux']:
    tar = tarfile.open('tools/%s.tar.xz' % f, 'r:xz')
    tar.extractall(path='tools/')
    tar.close()

print('[*] Downloading data.zip...')
download('https://www.dropbox.com/s/7f5uok2alxz9j1r/data.zip?dl=1', 'data.zip')

print('[*] Extracting data.zip...')
with ZipFile('data.zip', 'r') as z:
    z.extractall()

os.remove('data.zip')
print('[*] Completed!')
