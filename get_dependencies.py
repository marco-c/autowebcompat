import sys
import os
import tarfile
from zipfile import ZipFile
import requests
from rfc6266 import parse_requests_response
import posixpath

def download(url):
    response = requests.get(url, stream=True)
    filename = parse_requests_response(response).filename_unsafe

    default_filename = 'file'
    if filename is None:
        filename = default_filename
    filename = posixpath.basename(filename)
    filename = os.path.basename(filename)
    filename = filename.lstrip('.')
    if not filename:
        filename = default_filename

    if filename.rfind('.') == -1:
        print('Couldn\'t get filename for this url')
        return

    with open(filename, 'wb') as f:
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
            return
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


if sys.platform.startswith('linux'):
    url = 'https://www.dropbox.com/s/ziti4nkdzhgwg1n/linux.tar.xz?dl=1'
elif sys.platform.startswith('darwin'):
    url = 'https://www.dropbox.com/s/k4yifantsypy9xv/mac.tar.xz?dl=1'
elif sys.platform.startswith('win32'):
    url = 'https://www.dropbox.com/s/xskj9rpn2fjkra8/win32.tar.xz?dl=1'

print('[*] Downloading support files...')

try:
    name = download(url)
    print('[*] Extracting files...')
    with tarfile.open(name, 'r:xz') as f:
        f.extractall('.')
    os.remove(name)
except ValueError as e:
    print("No file found, "+e)


print('[*] Downloading data.zip...')
download('https://www.dropbox.com/s/nkf7a6jq13gmlnu/data.zip?dl=1')


try:
    with ZipFile('data.zip', 'r') as z:
        print('[*] Extracting data.zip...')
        z.extractall()
    os.remove('data.zip')
except:
    print('Invalid zip file ')

print('[*] Completed!')
