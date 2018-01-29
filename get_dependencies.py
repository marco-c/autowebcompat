import os
import shutil
import tarfile
from zipfile import ZipFile
import requests


for f in ['geckodriver', 'nightly', 'chromedriver', 'chrome-linux']:
    tar = tarfile.open('tools/%s.tar.xz' % f, 'r:xz')
    tar.extractall(path='tools/')
    tar.close()

r = requests.get('https://www.dropbox.com/s/7f5uok2alxz9j1r/data.zip?dl=1', stream=True)

with open('data.zip', 'wb') as f:
    r.raw.decode_content = True
    shutil.copyfileobj(r.raw, f)

with ZipFile('data.zip', 'r') as z:
    z.extractall()

os.remove('data.zip')
