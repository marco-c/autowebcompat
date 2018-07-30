from concurrent.futures import ThreadPoolExecutor
import glob
import json
import os
import random
import sys
import time
import traceback

from PIL import Image
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import TimeoutException

from autowebcompat import utils

MAX_THREADS = 5
MAX_INTERACTION_DEPTH = 7

if sys.platform.startswith('linux'):
    chrome_bin = 'tools/chrome-linux/chrome'
    nightly_bin = 'tools/nightly/firefox-bin'
elif sys.platform.startswith('darwin'):
    chrome_bin = 'tools/chrome.app/Contents/MacOS/chrome'
    nightly_bin = 'tools/Nightly.app/Contents/MacOS/firefox'
elif sys.platform.startswith('win32'):
    chrome_bin = 'tools\\Google\\Chrome\\Application\\chrome.exe'
    nightly_bin = 'tools\\Nightly\\firefox.exe'


utils.mkdir('data')

bugs = utils.get_bugs()
print(len(bugs))

with open('get_xpath.js', 'r') as f:
    get_xpath_script = f.read()


def set_timeouts(driver):
    driver.set_script_timeout(30)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(30)


def wait_loaded(driver):
    try:
        driver.execute_async_script("""
          let done = arguments[0];

          window.onload = done;
          if (document.readyState === 'complete') {
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


def get_element_properties(driver, child):
    child_properties = driver.execute_script("""
      let elem_properties = {
        tag: '',
        attributes: {},
      };

      for (let i = 0; i < arguments[0].attributes.length; i++) {
        elem_properties.attributes[arguments[0].attributes[i].name] = arguments[0].attributes[i].value;
      }
      elem_properties.tag = arguments[0].tagName;

      return elem_properties;
    """, child)

    return child_properties


def get_elements_with_properties(driver, elem_properties, children):
    elems_with_same_properties = []
    for child in children:
        child_properties = get_element_properties(driver, child)
        if child_properties == elem_properties:
            elems_with_same_properties.append(child)
    return elems_with_same_properties


def was_visited(current_path, visited_paths, elem_properties):
    current_path.append(elem_properties)
    if current_path in visited_paths:
        current_path.pop()
        return True
    else:
        return False


def visit(current_path, visited_paths):
    visited_paths.append(current_path[:])
    return


def do_something(driver, visited_paths, current_path, elem_properties=None):
    elem = None

    body = driver.find_elements_by_tag_name('body')
    assert len(body) == 1
    body = body[0]

    buttons = body.find_elements_by_tag_name('button')
    links = body.find_elements_by_tag_name('a')
    inputs = body.find_elements_by_tag_name('input')
    selects = body.find_elements_by_tag_name('select')
    children = buttons + links + inputs + selects

    if elem_properties is None:
        random.shuffle(children)
        children_to_ignore = []  # list of elements with same properties to ignore

        for child in children:
            if child in children_to_ignore:
                continue

            # Get all the properties of the child.
            elem_properties = get_element_properties(driver, child)

            # we check if the path has been visited previously
            if was_visited(current_path, visited_paths, elem_properties):
                continue

            # If the element is not displayed or is disabled, the user can't interact with it. Skip
            # non-displayed/disabled elements, since we're trying to mimic a real user.
            if not child.is_displayed() or not child.is_enabled():
                current_path.pop()
                continue

            elem = child

            # We mark the current path as visited
            elems = get_elements_with_properties(driver, elem_properties, children)
            if len(elems) == 1:
                elem = child
                break
            else:
                children_to_ignore.extend(elems)
            visit(current_path, visited_paths)
            break
    else:
        if 'id' not in elem_properties['attributes'].keys():
            elems = get_elements_with_properties(driver, elem_properties, children)
            assert len(elems) == 1
            elem = elems[0]
        else:
            elem_id = elem_properties['attributes']['id']
            elem = driver.find_element_by_id(elem_id)

    if elem is None:
        return None

    driver.execute_script('arguments[0].scrollIntoView();', elem)

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
        elif input_type == 'submit':
            elem.click()
        elif input_type == 'color':
            driver.execute_script("arguments[0].value = '#ff0000'", elem)
        else:
            raise Exception('Unsupported input type: %s' % input_type)
    elif elem.tag_name == 'select':
        for option in elem.find_elements_by_tag_name('option'):
            if option.text != '':
                option.click()
                break

    close_all_windows_except_first(driver)

    return elem_properties


def screenshot(driver, bug_id, browser, seq_no):
    WINDOW_HEIGHT = 732
    WINDOW_WIDTH = 412
    page_height = driver.execute_script('return document.body.scrollHeight;')
    page_width = driver.execute_script('return document.body.scrollWidth;')
    height = 0
    while height < page_height:
        width = 0
        while width < page_width:
            file_name = utils.create_file_name(bug_id=bug_id, browser=browser, width=str(width), height=str(height), seq_no=seq_no) + '.png'
            file_name = os.path.join('data', file_name)
            driver.execute_script('window.scrollTo(arguments[0], arguments[1]);', width, height)
            driver.get_screenshot_as_file(file_name)
            image = Image.open(file_name)
            image.save(file_name)
            width += WINDOW_WIDTH
        height += WINDOW_HEIGHT


def get_domtree(driver, bug_id, browser, seq_no):
    file_name = 'dom_' + utils.create_file_name(bug_id=bug_id, browser=browser, seq_no=seq_no) + '.txt'
    file_name = os.path.join('data', file_name)
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(driver.execute_script('return document.documentElement.outerHTML'))


def get_coordinates(driver, bug_id, browser, seq_no):
    dom_tree = etree.HTML(driver.execute_script('return document.documentElement.outerHTML'))
    dom_element_tree = etree.ElementTree(dom_tree)
    loc_dict = {}
    dom_tree_elements = [elem for elem in dom_tree.iter(tag=etree.Element)]
    web_elements = driver.find_elements_by_css_selector('*')
    dom_xpaths = []

    for element in dom_tree_elements:
        dom_xpaths.append(dom_element_tree.getpath(element))

    for element in web_elements:
        xpath = driver.execute_script(get_xpath_script, element)

        if xpath in dom_xpaths:
            loc_dict[xpath] = element.size
            loc_dict[xpath].update(element.location)
            dom_xpaths.remove(xpath)

    for xpath in dom_xpaths:
        try:
            element = driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            continue
        loc_dict[xpath] = element.size
        loc_dict[xpath].update(element.location)

    file_name = 'loc_' + utils.create_file_name(bug_id=bug_id, browser=browser, seq_no=seq_no) + '.txt'
    file_name = os.path.join('data', file_name)
    with open(file_name, 'w') as f:
        json.dump(loc_dict, f)


def get_screenshot_and_domtree(driver, bug_id, browser, seq_no=None):
    wait_loaded(driver)
    screenshot(driver, bug_id, browser, seq_no)
    get_domtree(driver, bug_id, browser, seq_no)
    get_coordinates(driver, bug_id, browser, seq_no)


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
    for elem_properties in current_path:
        do_something(firefox_driver, visited_paths, current_path, elem_properties)
        do_something(chrome_driver, visited_paths, current_path, elem_properties)


def run_test_both(bug, firefox_driver, chrome_driver):
    print('Testing %s (bug %d) in %s' % (bug['url'], bug['id'], 'firefox'))

    try:
        firefox_driver.get(bug['url'])
    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    get_screenshot_and_domtree(firefox_driver, str(bug['id']), 'firefox')
    print('Testing %s (bug %d) in %s' % (bug['url'], bug['id'], 'chrome'))

    try:
        chrome_driver.get(bug['url'])
    except TimeoutException as e:
        # Ignore timeouts, as they are too frequent.
        traceback.print_exc()
        print('Continuing...')

    get_screenshot_and_domtree(chrome_driver, str(bug['id']), 'chrome')

    visited_paths = []
    current_path = []
    while True:
        elem_properties = do_something(firefox_driver, visited_paths, current_path)
        print('  - Using %s' % elem_properties)
        if elem_properties is None:
            if not current_path:
                print('============= Completed (%d) =============' % bug['id'])
                break
            current_path.pop()
            jump_back(current_path, firefox_driver, chrome_driver, visited_paths, bug)
            continue

        do_something(chrome_driver, visited_paths, current_path, elem_properties)
        with open('data/%d.txt' % bug['id'], 'a+') as f:
            line_number = count_lines(bug['id'])
            f.seek(2, 0)
            for element in current_path:
                f.write(json.dumps(element) + '\n')
            f.write('\n')

        get_screenshot_and_domtree(firefox_driver, str(bug['id']), 'firefox', str(line_number))
        get_screenshot_and_domtree(chrome_driver, str(bug['id']), 'chrome', str(line_number))

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
firefox_profile.set_preference('general.useragent.override', 'Mozilla/5.0 (Android 6.0.1; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0')
firefox_profile.set_preference('intl.accept_languages', 'it')
firefox_profile.set_preference('media.volume_scale', '0.0')
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_bin
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--hide-scrollbars')
chrome_options.add_argument('--window-size=412,732')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5 Build/M4B30Z) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36')
chrome_options.add_argument('--lang=it')
chrome_options.add_argument('--mute-audio')


def main(bugs):
    firefox_driver = webdriver.Firefox(firefox_profile=firefox_profile, firefox_binary=nightly_bin)
    chrome_driver = webdriver.Chrome(chrome_options=chrome_options)
    run_tests(firefox_driver, chrome_driver, bugs)


if __name__ == '__main__':
    random.shuffle(bugs)
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for i in range(MAX_THREADS):
            executor.submit(main, bugs[i::MAX_THREADS])
