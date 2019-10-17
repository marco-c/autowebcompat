import os

from selenium import webdriver

from autowebcompat.utils import get_browser_bin


class Driver:

    def __init__(self):
        chrome_bin, nightly_bin = get_browser_bin()

        os.environ['PATH'] += os.pathsep + os.path.abspath('tools')
        os.environ['MOZ_HEADLESS'] = '1'
        os.environ['MOZ_HEADLESS_WIDTH'] = '412'
        os.environ['MOZ_HEADLESS_HEIGHT'] = '808'
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('general.useragent.override',
                                       'Mozilla/5.0 (Android 6.0.1; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = chrome_bin
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=412,732')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5 Build/M4B30Z) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36')

        self.firefox_driver = webdriver.Firefox(firefox_profile=firefox_profile, firefox_binary=nightly_bin)
        self.chrome_driver = webdriver.Chrome(chrome_options=chrome_options)

    def quit(self):
        self.firefox_driver.quit()
        self.chrome_driver.quit()

    @property
    def firefox(self):
        return self.firefox_driver

    @property
    def chrome(self):
        return self.chrome_driver
