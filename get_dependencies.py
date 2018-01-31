import os
import tarfile
from zipfile import ZipFile
from utils import download


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
