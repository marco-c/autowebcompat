import csv
import difflib
import os
import re

from lxml import etree

ignoredAttrib = {'style', 'type'}
matched21 = {}
matched12 = {}
nodes_info = {1: {}, 2: {}}
chrome_tree = None
firefox_tree = None
THRESHOLD_LEVEL = 0.75
THRESHOLD_GLOBAL = 0.85
folder = 'data'
dom_files_chrome = ['_'.join(f.split('_')[:-1]) for f in os.listdir(folder) if 'dom' in f and 'chrome' in f]
dom_files_firefox = ['_'.join(f.split('_')[:-1]) for f in os.listdir(folder) if 'dom' in f and 'firefox' in f]
dom_files = list(set(dom_files_firefox) & set(dom_files_chrome))


def processAttributes(attrib):
    for key in ignoredAttrib:
        attrib.pop(key, None)
    return attrib


def cleanAndCompare(str1, str2):
    str1 = re.sub(r'[\'\'\\s]', '', str1)
    str2 = re.sub(r'[\'\'\\s]', '', str2)
    return str1 == str2


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
    xPath1 = chrome_tree.getpath(x)
    xPath2 = firefox_tree.getpath(y)
    if xPath1 == xPath2:
        xPathSim = 1
    else:
        xPathSim = difflib.SequenceMatcher(None, xPath1, xPath2).ratio()
    attrib_x = processAttributes(x.attrib)
    attrib_y = processAttributes(y.attrib)
    attribSim = getMapSimilarity(attrib_x, attrib_y)
    return XPATH * xPathSim + ATTRIB * attribSim


def ExactMatchVisitor(root1, root2):
    global matched21, matched12
    for node1 in root1.iter(tag=etree.Element):
        for node2 in root2.iter(tag=etree.Element):
            if node1.tag == node2.tag:
                if node2 not in matched21.keys():
                    matchIndex = calculateMatchIndex(node1, node2)
                    if matchIndex == 1.0:
                        matched12[node1] = node2
                        matched21[node2] = node1
                        break


def AssignLevelVisitor(root, sno):
    levels = []
    for node in root.iter(tag=etree.Element):
        if node.getparent() is None:
            nodes_info[sno][node]['level'] = 0
            levels.append([])
            levels[0].append(node)
        else:
            nodes_info[sno][node]['level'] = nodes_info[sno][node.getparent()]['level'] + 1
            if len(levels) == nodes_info[sno][node]['level']:
                levels.append([])
            levels[nodes_info[sno][node]['level']].append(node)
    return levels


def ApproxMatchVisitor(worklist, root2):
    global matched21, matched12
    for node1 in worklist:
        bestMatchIndex = 0
        bestMatchNode = None
        for node2 in root2.iter(tag=etree.Element):
            if node1.tag == node2.tag:
                if node2 not in matched21.keys():
                    matchIndex = calculateMatchIndex(node1, node2)
                    if matchIndex > THRESHOLD_GLOBAL and matchIndex > bestMatchIndex:
                        bestMatchIndex = matchIndex
                        bestMatchNode = node2
        if bestMatchNode is not None:
            matched12[node1] = bestMatchNode
            matched21[bestMatchNode] = node1


def do_match(root1, root2):
    global matched21, matched12
    # 1. perfect matching
    ExactMatchVisitor(root1, root2)

    # Assign Levels
    AssignLevelVisitor(root1, 1)
    levels2 = AssignLevelVisitor(root2, 2)
    unmatched_nodes = [node for node in set(chrome_etree.iter(tag=etree.Element)) - set(matched12.keys())]
    worklist = []

    # 2. level matching
    for node in unmatched_nodes:
        level = nodes_info[1][node]['level']
        if level < len(levels2):
            lnodes = levels2[level]
            bestMatchIndex = 0
            bestMatchNode = None
            for ln in lnodes:
                if ln not in matched21.keys():
                    matchIndex = calculateMatchIndex(node, ln)
                    if matchIndex > THRESHOLD_LEVEL and matchIndex > bestMatchIndex:
                        bestMatchIndex = matchIndex
                        bestMatchNode = ln
            if bestMatchNode is not None:
                matched12[node] = bestMatchNode
                matched21[bestMatchNode] = node
            else:
                worklist.append(node)

    # 3. Approximate global matching
    ApproxMatchVisitor(worklist, root2)


results = []
for dom_file in dom_files:
    matched21 = {}
    matched12 = {}
    chrome_dom_file = os.path.join(folder, dom_file + '_chrome.txt')
    firefox_dom_file = os.path.join(folder, dom_file + '_firefox.txt')
    print(chrome_dom_file)
    print(firefox_dom_file)

    with open(chrome_dom_file, 'r') as f:
        chrome_dom = f.read()

    with open(firefox_dom_file, 'r') as f:
        firefox_dom = f.read()

    chrome_etree = etree.HTML(chrome_dom)
    firefox_etree = etree.HTML(firefox_dom)
    chrome_tree = etree.ElementTree(chrome_etree)
    firefox_tree = etree.ElementTree(firefox_etree)

    for node in chrome_etree.iter(tag=etree.Element):
        nodes_info[1][node] = {}

    for node in firefox_etree.iter(tag=etree.Element):
        nodes_info[2][node] = {}

    chrome_nodes = list(chrome_etree.iter(tag=etree.Element))
    firefox_nodes = list(firefox_etree.iter(tag=etree.Element))

    print('Chrome Nodes : %d' % len(chrome_nodes))
    print('Firefox Nodes : %d' % len(firefox_nodes))

    # Below condition is not implemented in xpert. Since algorithm is slow, this is just a check.
    if len(chrome_nodes) + len(firefox_nodes) > 1700:
        print('Large number of nodes to match -- skipping')
        continue

    do_match(chrome_etree, firefox_etree)
    print('Matched Nodes : %d\n\n' % len(matched21))

    image_name = '_'.join(dom_file.split('_')[1:])

    if len(matched21) == min(len(chrome_nodes), len(firefox_nodes)):
        label = 'y'
    else:
        label = 'n'
    results.append([image_name, label, len(matched21), len(chrome_nodes), len(firefox_nodes)])


with open('dom_test_labels.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow(['Image Name', 'Label', 'Nodes Matched', 'Nodes Chrome', 'Nodes Firefox'])
    for row in results:
        writer.writerow(row)
