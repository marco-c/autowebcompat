import os

from lxml import etree


def compare_doms(d1, d2):
    # match tag names
    if d1.tag != d2.tag:
        print('Tags mismatched \nCHROME : %s \nFIREFOX : %s' % (d1.tag, d2.tag))
        return False

    # match attributes
    for attribute_key in d1.attrib:
        if attribute_key not in d2.attrib:
            print('Attribute not found %s not in 2 (firefox)' % attribute_key)
            # return False
        elif d1.attrib[attribute_key] != d2.attrib[attribute_key]:
            print('Attribute values for (%s) mismatched \nCHROME : %s \nFIREFOX : %s' % (attribute_key, d1.attrib[attribute_key], d2.attrib[attribute_key]))
            # return False

    for attribute_key in d2.attrib:
        if attribute_key not in d1.attrib:
            print('Attribute not found %s not in 1 (chrome)' % attribute_key)
            # return False
        elif d1.attrib[attribute_key] != d2.attrib[attribute_key]:
            print('Attribute values for (%s) mismatched \nCHROME : %s \nFIREFOX : %s' % (attribute_key, d1.attrib[attribute_key], d2.attrib[attribute_key]))
            # return False

    # match number of child nodes
    if len(d1) != len(d2):
        print('Number of child nodes mismatched \nCHROME : %d \nFIREFOX : %d' % (len(d1), len(d2)))
        # return False

    # match child doms
    for c1, c2 in zip(d1, d2):
        if not compare_doms(c1, c2):
            return False
    return True


folder = 'data'
dom_files = [f for f in os.listdir(folder) if 'dom' in f and 'chrome' in f]

for file in dom_files:
    chrome_dom_file = os.path.join(folder, file)
    firefox_dom_file = os.path.join(folder, file.replace('chrome', 'firefox'))
    print(chrome_dom_file)
    print(firefox_dom_file)
    with open(chrome_dom_file, 'r') as f:
        chrome_dom = f.read()
    with open(firefox_dom_file, 'r') as f:
        firefox_dom = f.read()
    print(compare_doms(etree.HTML(chrome_dom), etree.HTML(firefox_dom)))
    input()
