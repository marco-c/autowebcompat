from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
import time
import random
import traceback
import glob
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, NoSuchWindowException, TimeoutException

from autowebcompat import utils

MAX_THREADS = 5
MAX_INTERACTION_DEPTH = 7

if sys.platform.startswith("linux"):
    chrome_bin = "tools/chrome-linux/chrome"
    nightly_bin = 'tools/nightly/firefox-bin'
elif sys.platform.startswith("darwin"):
    chrome_bin = "tools/chrome.app/Contents/MacOS/chrome"
    nightly_bin = 'tools/Nightly.app/Contents/MacOS/firefox'
elif sys.platform.startswith("win32"):
    chrome_bin = 'tools\\Google\\Chrome\\Application\\chrome.exe'
    nightly_bin = 'tools\\Nightly\\firefox.exe'


utils.mkdir('data')

bugs = utils.get_bugs()
print(len(bugs))


def set_timeouts(driver):
    driver.set_script_timeout(30)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(30)


def wait_loaded(driver):
    try:
        driver.execute_async_script("""
          let done = arguments[0];

          window.onload = done;
          if (document.readyState === "complete") {
            done();
          }
        """)
    except:  # noqa: E722
        traceback.print_exc()
        print('Continuing...')

    # We hope the page is fully loaded in 7 seconds.
    time.sleep(7)

    try:
        driver.execute_async_script("""
          window.requestIdleCallback(arguments[0], {
            timeout: 60000
          });
        """)
    except:  # noqa: E722
        traceback.print_exc()
        print('Continuing...')


def close_all_windows_except_first(driver):
    windows = driver.window_handles

    for window in windows[1:]:
        driver.switch_to_window(window)
        driver.close()

    while True:
        try:
            alert = driver.switch_to_alert()
            alert.dismiss()
        except (NoAlertPresentException, NoSuchWindowException):
            break

    driver.switch_to_window(windows[0])


def get_all_attributes(driver, child):
    child_attributes = driver.execute_script("""
      let elem_attribute = {};

      for (let i = 0; i < arguments[0].attributes.length; i++) {
        elem_attribute[arguments[0].attributes[i].name] = arguments[0].attributes[i].value;
      }
      return elem_attribute;
    """, child)

    return child_attributes


def was_visited(current_path, visited_paths, elem_attributes):
    current_path.append(elem_attributes)
    if current_path in visited_paths:
        current_path.pop()
        return True
    else:
        return False


def visit(current_path, visited_paths):
    visited_paths.append(current_path[:])
    return


def do_something(driver, visited_paths, current_path, elem_attributes=None):
    elem = None
    if elem_attributes is None:
        body = driver.find_elements_by_tag_name('body')
        assert len(body) == 1
        body = body[0]

        buttons = body.find_elements_by_tag_name('button')
        links = body.find_elements_by_tag_name('a')
        inputs = body.find_elements_by_tag_name('input')
        children = buttons + links + inputs

        random.shuffle(children)

        for child in children:
            # Get all the attributes of the child.
            elem_attributes = get_all_attributes(driver, child)

            # we check if the path has been visited previously
            if was_visited(current_path, visited_paths, elem_attributes):
                continue

            # If the element is not displayed or is disabled, the user can't interact with it. Skip
            # non-displayed/disabled elements, since we're trying to mimic a real user.
            if not child.is_displayed() or not child.is_enabled():
                current_path.pop()
                continue

            elem = child

            # We mark the current path as visited
            visit(current_path, visited_paths)
            break
    else:
        if 'id' not in elem_attributes.keys():
            body = driver.find_elements_by_tag_name('body')
            assert len(body) == 1
            body = body[0]

            buttons = body.find_elements_by_tag_name('button')
            links = body.find_elements_by_tag_name('a')
            inputs = body.find_elements_by_tag_name('input')
            children = buttons + links + inputs

            for child in children:
                # Get all the attributes of the child.
                if elem_attributes == get_all_attributes(driver, child):
                    elem = child
                    break
        else:
            elem_id = elem_attributes['id']
            elem = driver.find_element_by_id(elem_id)

    if elem is None:
        return None

    driver.execute_script("arguments[0].scrollIntoView();", elem)

    if elem.tag_name in ['button', 'a']:
        elem.click()
    elif elem.tag_name == 'input':
        input_type = elem.get_attribute('type')
        if input_type == 'url':
            elem.send_keys('http://www.mozilla.org/')
        elif input_type == 'text':
            elem.send_keys('marco')
        elif input_type == 'email':
            elem.send_keys('prova@email.it')
        elif input_type == 'password':
            elem.send_keys('aMildlyComplexPasswordIn2017')
        elif input_type == 'checkbox':
            elem.click()
        elif input_type == 'number':
            elem.send_keys('3')
        elif input_type == 'radio':
            elem.click()
        elif input_type == 'search':
            elem.clear()
            elem.send_keys('quick search')
        elif input_type == 'color':
            driver.execute_script("arguments[0].value = '#ff0000'", elem)
        else:
            raise Exception('Unsupported input type: %s' % input_type)

    close_all_windows_except_first(driver)

    return elem_attributes


def screenshot(driver, file_path):
    wait_loaded(driver)

    driver.get_screenshot_as_file(file_path)
    image = Image.open(file_path)
    image.save(file_path)


def count_lines(bug_id):
    try:
        with open('data/%d.txt' % bug_id) as f:
            return sum(1 for line in f)
    except IOError:
        return 0


# We restart from the start and follow the saved sequence
def jump_back(current_path, firefox_driver, chrome_driver, visited_paths, bug):
    firefox_driver.get(bug['url'])
    chrome_driver.get(bug['url'])
    for elem_attributes in current_path:
        do_something(firefox_driver, visited_paths, current_path, elem_attributes)
        do_something(chrome_driver, visited_paths, current_path, elem_attributes)


def run_test_both(bug, firefox_driver, chrome_driver):
    print('Testing %s (bug %d) in %s' % (bug['url'], bug['id'], "firefox"))

    try:
        firefox_driver.get(bug['url'])
    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    screenshot(firefox_driver, 'data/%d_%s.png' % (bug['id'], "firefox"))
    print('Testing %s (bug %d) in %s' % (bug['url'], bug['id'], "chrome"))

    try:
        chrome_driver.get(bug['url'])
    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    screenshot(chrome_driver, 'data/%d_%s.png' % (bug['id'], "chrome"))

    visited_paths = []
    current_path = []
    while True:
        elem_attributes = do_something(firefox_driver, visited_paths, current_path)

        if elem_attributes is None:
            if not current_path:
                print("============= Completed (%d) =============" % bug['id'])
                break
            current_path.pop()
            jump_back(current_path, firefox_driver, chrome_driver, visited_paths, bug)
            continue

        do_something(chrome_driver, visited_paths, current_path, elem_attributes)
        with open("data/%d.txt" % bug['id'], 'a+') as f:
            line_number = count_lines(bug['id'])
            f.seek(2, 0)
            for element in current_path:
                f.write(json.dumps(element) + '\n')
            f.write('\n')

        image_file = "data/%d_%d_firefox.png" % (bug['id'], line_number)
        screenshot(firefox_driver, '%s' % (image_file))
        image_file = "data/%d_%d_chrome.png" % (bug['id'], line_number)
        screenshot(chrome_driver, '%s' % (image_file))

        if len(current_path) == MAX_INTERACTION_DEPTH:
            current_path.pop()
            jump_back(current_path, firefox_driver, chrome_driver, visited_paths, bug)


def run_tests(firefox_driver, chrome_driver, bugs):
    set_timeouts(firefox_driver)
    set_timeouts(chrome_driver)

    for bug in bugs:
        try:
            # We attempt to regenerate everything when either
            # a) we haven't generated the main screenshot for Firefox or Chrome, or
            # b) we haven't generated any item of the sequence for Firefox, or
            # c) there are items in the Firefox sequence that we haven't generated for Chrome.
            lines_written = count_lines(bug['id'])
            number_of_ff_scr = len(glob.glob('data/%d_*_firefox.png' % bug['id']))
            number_of_ch_scr = len(glob.glob('data/%d_*_chrome.png' % bug['id']))
            if not os.path.exists('data/%d_firefox.png' % bug['id']) or \
               not os.path.exists('data/%d_chrome.png' % bug['id']) or \
               lines_written == 0 or \
               number_of_ff_scr != number_of_ch_scr:
                for f in glob.iglob('data/%d*' % bug['id']):
                    os.remove(f)
                run_test_both(bug, firefox_driver, chrome_driver)

        except:  # noqa: E722
            traceback.print_exc()
            close_all_windows_except_first(firefox_driver)
            close_all_windows_except_first(chrome_driver)

    firefox_driver.quit()
    chrome_driver.quit()


os.environ['PATH'] += os.pathsep + os.path.abspath('tools')
os.environ['MOZ_HEADLESS'] = '1'
os.environ['MOZ_HEADLESS_WIDTH'] = '412'
os.environ['MOZ_HEADLESS_HEIGHT'] = '808'
firefox_profile = webdriver.FirefoxProfile()
firefox_profile.set_preference("general.useragent.override", "Mozilla/5.0 (Android 6.0.1; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0")
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_bin
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=412,732")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5 Build/M4B30Z) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36")


def main(bugs):
    firefox_driver = webdriver.Firefox(firefox_profile=firefox_profile, firefox_binary=nightly_bin)
    chrome_driver = webdriver.Chrome(chrome_options=chrome_options)
    run_tests(firefox_driver, chrome_driver, bugs)


if __name__ == '__main__':
    random.shuffle(bugs)
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for i in range(MAX_THREADS):
            executor.submit(main, bugs[i::MAX_THREADS])
