import csv
import difflib
import functools
import json
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
tagsIgnore = {"A", "AREA", "B", "BLOCKQUOTE",
              "BR", "CANVAS", "CENTER", "CSACTIONDICT", "CSSCRIPTDICT", "CUFON",
              "CUFONTEXT", "DD", "EM", "EMBED", "FIELDSET", "FONT", "FORM",
              "HEAD", "HR", "I", "LABEL", "LEGEND", "LINK", "MAP", "MENUMACHINE",
              "META", "NOFRAMES", "NOSCRIPT", "OBJECT", "OPTGROUP", "OPTION",
              "PARAM", "S", "SCRIPT", "SMALL", "SPAN", "STRIKE", "STRONG",
              "STYLE", "TBODY", "TITLE", "TR", "TT", "U", "UL"}
tagsContainer = {"DD", "DIV", "DT", "P",
                 "TD", "TR"}
SIZE_DIFF_THRESH = 0.7
SIZE_DIFF_IGNORE = 0.1


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


def isLayoutNode(node, xpath, loc):
    if node.tag.upper() in tagsIgnore:
        return False
    if xpath not in loc:
        return False
    x1 = loc[xpath]['x']
    y1 = loc[xpath]['y']
    height = loc[xpath]['height']
    width = loc[xpath]['width']
    x2 = x1 + width
    y2 = y1 + height

    if x1 < 0 or y1 < 0 or x2 <= 0 or y2 <= 0:
        return False
    negligible_dim = 5
    if height <= negligible_dim or width <= negligible_dim:
        return False
    if node.tag.upper() in tagsContainer:
        if len(node) == 0:
            return False
        hasVisibleChild = False
        for child in node:
            if child.text is not None or child.tag.upper() not in tagsIgnore:
                hasVisibleChild = True
        if hasVisibleChild is False:
            return False
    return True


def contains(n, node, loc):
    n_x1 = loc[n]['x']
    n_y1 = loc[n]['y']
    n_x2 = n_x1 + loc[n]['width']
    n_y2 = n_y1 + loc[n]['height']

    node_x1 = loc[node]['x']
    node_y1 = loc[node]['y']
    node_x2 = node_x1 + loc[node]['width']
    node_y2 = node_y1 + loc[node]['height']

    if n_x1 <= node_x1 and n_y1 <= node_y1 and n_x2 >= node_x2 and n_y2 >= node_y2:
        return True
    return False


def get_area(node, loc):
    return loc[node]['height'] * loc[node]['width']


def hasSignificantSizeDiff(p, c):
    pcSizeDiff = c / p
    if pcSizeDiff < SIZE_DIFF_THRESH and pcSizeDiff > SIZE_DIFF_IGNORE:
        return True
    return False


def populate_alignments(parent, child, loc):
    dH_delta = 5
    dW_delta = 5
    edge_info = {'SizeDiffX': False,
                 'hFill': False,
                 'LeftJustified': False,
                 'RightJustified': False,
                 'Centered': False,
                 'SizeDiffY': False,
                 'vFill': False,
                 'TopAligned': False,
                 'BottomAligned': False,
                 'Middle': False
                 }
    p_x1 = loc[parent]['x']
    p_x2 = loc[parent]['x'] + loc[parent]['width']
    p_y1 = loc[parent]['y']
    p_y2 = loc[parent]['y'] + loc[parent]['height']

    c_x1 = loc[child]['x']
    c_x2 = loc[child]['x'] + loc[child]['width']
    c_y1 = loc[child]['y']
    c_y2 = loc[child]['y'] + loc[child]['height']

    px = (p_x1 + p_x2) / 2
    py = (p_y1 + p_y2) / 2
    cx = (c_x1 + c_x2) / 2
    cy = (c_y1 + c_y2) / 2

    pw = loc[parent]['width']
    cw = loc[child]['width']
    dW = cw / 3

    ph = loc[parent]['height']
    ch = loc[child]['height']
    dH = ch / 3

    if cw < 15 and pw < 15:
        return edge_info

    if hasSignificantSizeDiff(pw, cw):
        edge_info['SizeDiffX'] = True
        if abs(px - cx) <= dW_delta and abs(p_x1 - c_x1) <= dW_delta and abs(p_x2 - c_x2) <= dW_delta:
            edge_info['hFill'] = True
        else:
            if abs(c_x1 - p_x1) <= dW:
                edge_info['LeftJustified'] = True
            elif abs(c_x2 - p_x2) <= dW:
                edge_info['RightJustified'] = True
            elif abs(cx - px) <= dW:
                edge_info['Centered'] = True

    if hasSignificantSizeDiff(ph, ch):
        edge_info['SizeDiffY'] = True
        if abs(py - cy) <= dW_delta and abs(p_y1 - c_y1) <= dH_delta and abs(p_y2 - c_y2) <= dH_delta:
            edge_info['hFill'] = True
        else:
            if abs(c_y1 - p_y1) <= dH:
                edge_info['TopAligned'] = True
            elif abs(c_y2 - p_y2) <= dH:
                edge_info['BottomAligned'] = True
            elif abs(cy - py) <= dH:
                edge_info['Middle'] = True
    return edge_info


def populate_parent_edges(nodes, loc, contains_edge_info):
    cMap = {}
    while len(nodes) > 0:
        node = nodes[0]
        nodes.pop(0)
        parent = None
        for n in nodes:
            if contains(n, node, loc):
                if parent is not None and get_area(parent, loc) <= get_area(n, loc):
                    continue
                parent = n

        if parent is not None:
            if parent not in cMap:
                cMap[parent] = []
            cMap[parent].append(node)
            contains_edge_info[(parent, node)] = populate_alignments(parent, node, loc)
    return cMap


# 1 -> chrome 2 -> firefox
results = []
for dom_file in dom_files:
    if '768' not in dom_file:
        continue
    matched21 = {}
    matched12 = {}
    chrome_dom_file = os.path.join(folder, dom_file + '_chrome.txt')
    firefox_dom_file = os.path.join(folder, dom_file + '_firefox.txt')
    chrome_loc_file = os.path.join(folder, dom_file.replace('dom', 'loc') + '_chrome.txt')
    firefox_loc_file = os.path.join(folder, dom_file.replace('dom', 'loc') + '_firefox.txt')
    print(chrome_dom_file)
    print(firefox_dom_file)

    with open(chrome_dom_file, 'r') as f:
        chrome_dom = f.read()

    with open(firefox_dom_file, 'r') as f:
        firefox_dom = f.read()

    with open(chrome_loc_file, 'r') as f:
        chrome_loc = json.load(f)

    with open(firefox_loc_file, 'r') as f:
        firefox_loc = json.load(f)

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

    vertices_chrome = []
    vertices_firefox = []
    for chrome_node, firefox_node in matched12.items():
        chrome_xpath = chrome_tree.getpath(chrome_node)
        firefox_xpath = firefox_tree.getpath(firefox_node)

        if isLayoutNode(chrome_node, chrome_xpath, chrome_loc):
            vertices_chrome.append(chrome_xpath)

        if isLayoutNode(firefox_node, firefox_xpath, firefox_loc):
            vertices_firefox.append(firefox_xpath)

    vertices_chrome = sorted(vertices_chrome, key=lambda x: (chrome_loc[x]['height'] * chrome_loc[x]['width'], len(x)))
    vertices_firefox = sorted(vertices_firefox, key=lambda x: (firefox_loc[x]['height'] * firefox_loc[x]['width'], len(x)))

    chrome_contains_edge_info = {}
    firefox_contains_edge_info = {}
    chrome_cMap = populate_parent_edges(vertices_chrome[:], chrome_loc, chrome_contains_edge_info)
    firefox_cMap = populate_parent_edges(vertices_firefox[:], firefox_loc, firefox_contains_edge_info)
    # chrome_siblings = populate_sibling_edges(vertices_chrome[:], chrome_loc)
    # firefox_siblings = populate_sibling_edges(vertices_firefox[:], firefox_loc)
    # print(chrome_cMap)
    input()


with open('dom_test_labels.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow(['Image Name', 'Label', 'Nodes Matched', 'Nodes Chrome', 'Nodes Firefox'])
    for row in results:
        writer.writerow(row)
