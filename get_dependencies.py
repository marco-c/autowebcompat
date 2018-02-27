import sys
import os
import tarfile
import requests
from rfc6266 import parse_requests_response
import posixpath


def download(url):
    response = requests.get(url, stream=True)
    filename = parse_requests_response(response).filename_unsafe

    if filename is None:
        raise Exception('No filename could be found for this URL')

    filename = sanitize(filename)

    with open(filename, 'wb') as f:
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
    return filename


def sanitize(filename):
    filename = posixpath.basename(filename)
    filename = os.path.basename(filename)
    filename = filename.lstrip('.')
    return filename


if sys.platform.startswith('linux'):
    url = 'https://www.dropbox.com/s/ziti4nkdzhgwg1n/linux.tar.xz?dl=1'
elif sys.platform.startswith('darwin'):
    url = 'https://www.dropbox.com/s/k4yifantsypy9xv/mac.tar.xz?dl=1'
elif sys.platform.startswith('win32'):
    url = 'https://www.dropbox.com/s/xskj9rpn2fjkra8/win32.tar.xz?dl=1'

print('[*] Downloading support files...')
name = download(url)

print('[*] Extracting files...')
with tarfile.open(name, 'r:xz') as f:
    f.extractall('.')
os.remove(name)

print('[*] Completed!')
