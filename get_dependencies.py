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


if sys.platform.startswith('linux'):
    url = 'https://www.dropbox.com/s/ziti4nkdzhgwg1n/linux.tar.xz?dl=1'
    name = 'linux.tar.xz'
elif sys.platform.startswith('darwin'):
    url = 'https://www.dropbox.com/s/k4yifantsypy9xv/mac.tar.xz?dl=1'
    name = 'mac.tar.xz'
elif sys.platform.startswith('win32'):
    url = 'https://www.dropbox.com/s/xskj9rpn2fjkra8/win32.tar.xz?dl=1'
    name = 'win32.tar.xz'

print('[*] Downloading support files...')
download(url, name)

print('[*] Extracting files...')
f = tarfile.open(name, 'r:xz')
f.extractall('.')
f.close()

os.remove(name)

print('[*] Downloading data.zip...')
download('https://www.dropbox.com/s/7f5uok2alxz9j1r/data.zip?dl=1', 'data.zip')

print('[*] Extracting data.zip...')
with ZipFile('data.zip', 'r') as z:
    z.extractall()

os.remove('data.zip')
print('[*] Completed!')
