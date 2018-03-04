from autowebcompat.crawler import close_all_windows_except_first
from autowebcompat.driver import Driver


class TestCrawler:

    def setup_method(self):
        self.driver = Driver()

    def teardown_method(self):
        pass

    def test_close_all_windows_except_first(self):
        self.driver.firefox.execute_script("window.open('https://twitter.com')")
        self.driver.firefox.execute_script("window.open('https://google.com')")
        self.driver.chrome.execute_script("window.open('https://twitter.com')")
        self.driver.chrome.execute_script("window.open('https://google.com')")
        assert len(self.driver.firefox.window_handles) == 3, 'More than 3 windows are open'

        close_all_windows_except_first(self.driver.firefox)
        close_all_windows_except_first(self.driver.chrome)

        assert len(self.driver.firefox.window_handles) == 1
        assert len(self.driver.chrome.window_handles) == 1
