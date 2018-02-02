import os
import sys
import tarfile
from zipfile import ZipFile
import requests
from sys import platform as _platform


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


if _platform == "linux" or _platform == "linux2":  # linux
    osys = "linux"
elif _platform == "darwin":    # MAC OS X
    osys = "mac"


if osys == "linux":
    print('linux os detected !')
    print('[*] Downloading support files for linux ~ 108 mb')
    download('https://www.dropbox.com/s/3mosdy9tsf7pilh/linux.zip?dl=1' , 'linux.zip')
    print('[*] Extracting linux.zip...')
    with ZipFile('linux.zip' , 'r') as z:
        z.extractall("linux")
    print('[*] Extracting webdriver archives...')
    for f in ['geckodriver', 'nightly', 'chromedriver', 'chrome-linux']:
        tar = tarfile.open('linux/%s.tar.xz' % f, 'r:xz')
        tar.extractall(path ='tools/')
        tar.close()
    os.remove('linux.zip')
    os.system("rm -rf linux ")

elif osys == "mac":
    print('mac os detected !')
    print('[*] Downloading support files for mac ~ 150 mb')
    download('https://www.dropbox.com/s/k1szymmktj0e1pf/mac.zip?dl=1' , 'mac.zip')
    print('[*] Extracting mac.zip...')
    os.system("unzip mac.zip -d tools")
    os.system("cp tools/geckodriver" + " /usr/local/bin/ ")
    os.system("cp tools/chromedriver" + " /usr/local/bin/ ")
    os.remove('mac.zip')

print('[*] Support file Downloaded!')

print('[*] Downloading data.zip...')
download('https://www.dropbox.com/s/7f5uok2alxz9j1r/data.zip?dl=1', 'data.zip')

print('[*] Completed!')