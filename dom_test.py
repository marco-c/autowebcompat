import os
import re

import difflib
from lxml import etree

ignoredAttrib = {'style', 'type'}
matched = {}
tree1 = None
tree2 = None

folder = 'data'
dom_files = [f for f in os.listdir(folder) if 'dom' in f and 'chrome' in f]


def processAttributes(attrib):
    for key in ignoredAttrib:
        attrib.pop(key, None)
    return attrib


def cleanAndCompare(str1, str2):
    str1 = re.sub(r'[\'\"\\s]', '', str1)
    str2 = re.sub(r'[\'\"\\s]', '', str2)
    return str1 == str2                     # change to levenshtein (minimum edit distance) just thinking for src


def mapDiff(x, y):
    matchCount = 0
    for key in x.keys():
        if key in y.keys() and cleanAndCompare(x[key], y[key]):
            matchCount += 1

    for key in y.keys():
        if key in x.keys() and cleanAndCompare(x[key], y[key]):
            matchCount += 1
    return matchCount


def getMapSimilarity(x, y):
    if not x and not y:
        return 1

    total = len(x) + len(y)
    return mapDiff(x, y) / total


def calculateMatchIndex(x, y):
    XPATH = 0.75
    ATTRIB = 0.25
    xPath1 = tree1.getpath(x)
    xPath2 = tree2.getpath(y)
    xPathSim = difflib.SequenceMatcher(None, xPath1, xPath2).ratio()
    attrib_x = processAttributes(x.attrib)
    attrib_y = processAttributes(y.attrib)
    attribSim = getMapSimilarity(attrib_x, attrib_y)
    return XPATH * xPathSim + ATTRIB * attribSim


def ExactMatchVisitor(node, root):
    if root not in matched.keys():
        if node.tag == root.tag:
            matchIndex = calculateMatchIndex(node, root)
            if matchIndex == 1.0:
                matched[root] = node
                return True
    # print(list(root))
    for child in list(root):
        if ExactMatchVisitor(node, child):
            return True


def do_match(root1, root2):
    global matched
    # perfect matching
    worklist = []
    worklist.append(root1)
    while worklist:
        node = worklist.pop(0)
        ExactMatchVisitor(node, root2)
        for child in list(node):
            worklist.append(child)


for file in dom_files:
    matched = {}
    chrome_dom_file = os.path.join(folder, file)
    firefox_dom_file = os.path.join(folder, file.replace('chrome', 'firefox'))
    print(chrome_dom_file)
    print(firefox_dom_file)
    with open(chrome_dom_file, 'r') as f:
        chrome_dom = f.read()
    with open(firefox_dom_file, 'r') as f:
        firefox_dom = f.read()
    # print(compare_doms(etree.HTML(chrome_dom), etree.HTML(firefox_dom)))
    a = etree.HTML(chrome_dom)
    b = etree.HTML(firefox_dom)
    tree1 = etree.ElementTree(a)
    tree2 = etree.ElementTree(b)
    do_match(a, b)
    print(len(matched))
    # print(matched)
    # print(tree1.getpath(a[0]))
    # print(tree2.getpath(b[0]))
    print(len(list(b.iter())))
    print(len(list(a.iter())))
    # print(tree1.getpath(tree1.findall('.//div')[12]))
    # print()
    input()
