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
THRESHOLD_LEVEL = 0.75
THRESHOLD_GLOBAL = 0.85
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
    for node1 in root1.iter(tag=etree.Element):
        # print(ct)
        for node2 in root2.iter(tag=etree.Element):
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
    # ct  = 0
    for node1 in worklist:
        bestMatchIndex = 0
        bestMatchNode = None
        # print(ct)
        for node2 in root2.iter(tag=etree.Element):
            # ct += 1
            if node1.tag == node2.tag:
                if node2 not in matched21.keys():
                    matchIndex = calculateMatchIndex(node1, node2)
                    # print(tree1.getpath(node1), tree2.getpath(node2), matchIndex)
                    if matchIndex > THRESHOLD_GLOBAL and matchIndex > bestMatchIndex:
                        bestMatchIndex = matchIndex
                        bestMatchNode = node2
                        # print(tree1.getpath(node1))
                        # print(tree2.getpath(node2))
                        # print(matchIndex)
                        # input()
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
    unmatched_nodes = [node for node in set(a.iter(tag=etree.Element)) - set(matched12.keys())]
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


for file in dom_files:
    matched21 = {}
    matched12 = {}
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
    for node in a.iter(tag=etree.Element):
        nodes_info[1][node] = {}
    for node in b.iter(tag=etree.Element):
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
    print("Chrome Nodes : %d" % len(list(a.iter(tag=etree.Element))))
    print("Firefox Nodes : %d" % len(list(b.iter(tag=etree.Element))))

    if len(list(a.iter(tag=etree.Element))) + len(list(b.iter(tag=etree.Element))) > 1700:
        continue
    do_match(a, b)
    print("Matched Nodes : %d\n\n" % len(matched21))
    # print(tree1.getpath(tree1.findall('.//div')[12]))
    # print(tree1.getpath(tree1.findall('.//div')[12].getparent()))
    # print()
    input()
