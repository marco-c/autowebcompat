import os
import re

import difflib
from lxml import etree

ignoredAttrib = {'style', 'type'}
matched21 = {}
matched12 = {}
nodes_info = {1: {}, 2: {}}
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
    # ct  = 0
    for node1 in root1.iter():
        # print(ct)
        best_match = 0
        for node2 in root2.iter():
            # ct += 1
            if node1.tag == node2.tag:
                if node2 not in matched21.keys():
                    matchIndex = calculateMatchIndex(node1, node2)
                    # print(tree1.getpath(node1), tree2.getpath(node2), matchIndex)
                    if matchIndex == 1.0:
                        # print(tree1.getpath(node1))
                        # print(tree2.getpath(node2))
                        # print(matchIndex)
                        # input()
                        matched12[node1] = node2
                        matched21[node2] = node1
                        break
                    elif matchIndex > best_match:
                        best_match = matchIndex
                        best_match_node = node2
        if best_match >= 0.85:
            matched12[node1] = best_match_node
            matched21[best_match_node] = node1
            # print(tree1.getpath(node1))
            # print(tree2.getpath(best_match_node))
            # print(best_match)
            # input()
        # input()


def AssignLevelVisitor(root, sno):
    levels = []
    for node in root.iter():
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


def do_match(root1, root2):
    global matched21, matched12
    # perfect matching
    # Assign Levels
    # levels1 = AssignLevelVisitor(root1, 1)
    # levels2 = AssignLevelVisitor(root2, 2)
    ExactMatchVisitor(root1, root2)

    # print(list(nodes_info[1].keys()))
    # print(list(matched21.keys()))
    unmatched_nodes_chrome = [node for node in set(a.iter(tag=etree.Element)) - set(matched12.keys())]
    print("Unmatched Nodes chrome : %d" % len(unmatched_nodes_chrome))

    for node in unmatched_nodes_chrome:
        print(tree1.getpath(node), node.attrib)

    unmatched_nodes_firefox = [node for node in set(b.iter(tag=etree.Element)) - set(matched21.keys())]
    print("Unmatched Nodes firefox: %d" % len(unmatched_nodes_chrome))
    for node in unmatched_nodes_firefox:
        print(tree2.getpath(node), node.attrib)


for file in dom_files:
    # if '1211_0' not in file:
    #     continue
    matched21 = {}
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
    for node in a.iter(tag = etree.Element):
        nodes_info[1][node] = {}
    for node in b.iter(tag = etree.Element):
        nodes_info[2][node] = {}
    # print(nodes_info)
    l1 = list(a.iter(tag=etree.Element))
    l2 = list(b.iter(tag=etree.Element))
    s1 = []
    s2 = []
    # for i in range(len(l2)):
    #     s1.append(tree1.getpath(l1[i]))
    #     s2.append(tree2.getpath(l2[i]))
    #     print(s1[-1], s2[-1])
    #     input()
    # print(len(set(s2) & set(s1)))
    # print(matched21)
    # print(tree1.getpath(a[0]))
    # print(tree2.getpath(b[0]))
    print("Chrome Nodes : %d" % len(list(a.iter())))
    print("Firefox Nodes : %d" % len(list(b.iter())))

    if len(list(a.iter())) + len(list(b.iter())) > 1700:
        continue
    do_match(a, b)
    print("Matched Nodes : %d\n\n" % len(matched21))
    # print(tree1.getpath(tree1.findall('.//div')[12]))
    # print(tree1.getpath(tree1.findall('.//div')[12].getparent()))
    # print()
    # input()
