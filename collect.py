import json
import os
import sys
import time
import random
import traceback
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, NoSuchWindowException, TimeoutException

from autowebcompat import utils

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


def do_something(driver, elem_attributes=None):
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
            child_attributes = get_all_attributes(driver, child)

            # If the element is not displayed or is disabled, the user can't interact with it. Skip
            # non-displayed/disabled elements, since we're trying to mimic a real user.
            if not child.is_displayed() or not child.is_enabled():
                continue

            elem = child
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
                child_attributes = get_all_attributes(driver, child)
                if elem_attributes == child_attributes:
                    elem = child
                    break
        else:
            elem_id = elem_attributes['id']
            elem = driver.find_element_by_id(elem_id)

    if elem is None:
        return None

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
        else:
            raise Exception('Unsupported input type: %s' % input_type)

    close_all_windows_except_first(driver)

    return child_attributes


def screenshot(driver, file_path):
    wait_loaded(driver)

    driver.get_screenshot_as_file(file_path)
    image = Image.open(file_path)
    image.save(file_path)


def run_test(bug, browser, driver, op_sequence=None):
    print('Testing %s (bug %d) in %s' % (bug['url'], bug['id'], browser))

    try:
        driver.get(bug['url'])
    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    screenshot(driver, 'data/%d_%s.png' % (bug['id'], browser))

    saved_sequence = []
    try:
        max_iter = 7 if op_sequence is None else len(op_sequence)
        for i in range(0, max_iter):
            if op_sequence is None:
                elem_attributes = do_something(driver)
                if elem_attributes is None:
                    print('Can\'t find any element to interact with on %s for bug %d' % (bug['url'], bug['id']))
                    break
                saved_sequence.append(elem_attributes)
            else:
                elem_attributes = op_sequence[i]
                do_something(driver, elem_attributes)

            print('  - Using %s' % elem_attributes)
            image_file = str(bug['id']) + '_' + str(i) + '_' + browser
            screenshot(driver, 'data/%s.png' % (image_file))

    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    return saved_sequence


def run_tests(firefox_driver, chrome_driver):
    set_timeouts(firefox_driver)
    set_timeouts(chrome_driver)

    random.shuffle(bugs)

    for bug in bugs:
        try:
            # Assume that if we generated the main file, we also generated the one with
            # the sequence of operations (TODO: don't assume, check!)
            # TODO: If only Chrome is missing, don't regenerate Firefox too, but read the
            # sequence of operations from the files.
            if not os.path.exists('data/%d_firefox.png' % bug['id']) or\
               not os.path.exists('data/%d_chrome.png' % bug['id']):
                sequence = run_test(bug, 'firefox', firefox_driver)
                run_test(bug, 'chrome', chrome_driver, sequence)

                with open("data/%d.txt" % bug['id'], 'w') as f:
                    for element in sequence:
                        f.write(json.dumps(element) + '\n')

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
firefox_driver = webdriver.Firefox(firefox_profile=firefox_profile, firefox_binary=nightly_bin)
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_bin
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=412,732")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5 Build/M4B30Z) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36")
chrome_driver = webdriver.Chrome(chrome_options=chrome_options)

run_tests(firefox_driver, chrome_driver)
