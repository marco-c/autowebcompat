import csv
import difflib
import json
import os
import re

from lxml import etree

ignoredAttrib = {'style', 'type'}
matched21 = {}
matched12 = {}
matched12_xpaths = {}

nodes_info = {1: {}, 2: {}}
chrome_tree = None
firefox_tree = None
THRESHOLD_LEVEL = 0.75
THRESHOLD_GLOBAL = 0.85
folder = 'data'
dom_files_chrome = ['_'.join(f.split('_')[:-1]) for f in os.listdir(folder) if 'dom' in f and 'chrome' in f]
dom_files_firefox = ['_'.join(f.split('_')[:-1]) for f in os.listdir(folder) if 'dom' in f and 'firefox' in f]
dom_files = list(set(dom_files_firefox) & set(dom_files_chrome))
tagsIgnore = {'A', 'AREA', 'B', 'BLOCKQUOTE',
              'BR', 'CANVAS', 'CENTER', 'CSACTIONDICT', 'CSSCRIPTDICT', 'CUFON',
              'CUFONTEXT', 'DD', 'EM', 'EMBED', 'FIELDSET', 'FONT', 'FORM',
              'HEAD', 'HR', 'I', 'LABEL', 'LEGEND', 'LINK', 'MAP', 'MENUMACHINE',
              'META', 'NOFRAMES', 'NOSCRIPT', 'OBJECT', 'OPTGROUP', 'OPTION',
              'PARAM', 'S', 'SCRIPT', 'SMALL', 'SPAN', 'STRIKE', 'STRONG',
              'STYLE', 'TBODY', 'TITLE', 'TR', 'TT', 'U', 'UL'}
tagsContainer = {'DD', 'DIV', 'DT', 'P',
                 'TD', 'TR'}
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


def calcError(a, b, delta):
    return abs(a - b) / delta


def populate_contain_alignments(parent, child, loc):
    deltaH = 5
    deltaW = 5
    edge_info = {'SizeDiffX': False,
                 'xError': 0,
                 'hFill': False,
                 'LeftJustified': False,
                 'RightJustified': False,
                 'Centered': False,
                 'SizeDiffY': False,
                 'yError': 0,
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
        if abs(px - cx) <= deltaW and abs(p_x1 - c_x1) <= deltaW and abs(p_x2 - c_x2) <= deltaW:
            edge_info['hFill'] = True
        else:
            if abs(c_x1 - p_x1) <= dW:
                edge_info['LeftJustified'] = True
                edge_info['xError'] = calcError(c_x1, p_x1, dW)
            elif abs(c_x2 - c_x2) <= dW:
                edge_info['RightJustified'] = True
                edge_info['xError'] = calcError(c_x2, c_x2, dW)
            elif abs(cx - px) <= dW:
                edge_info['Centered'] = True
                edge_info['xError'] = calcError(cx, px, dW)

    if hasSignificantSizeDiff(ph, ch):
        edge_info['SizeDiffY'] = True
        if abs(py - cy) <= deltaW and abs(p_y1 - c_y1) <= deltaH and abs(p_y2 - c_y2) <= deltaH:
            edge_info['hFill'] = True
        else:
            if abs(c_y1 - p_y1) <= dH:
                edge_info['TopAligned'] = True
                edge_info['yError'] = calcError(c_y1, p_y1, dH)
            elif abs(c_y2 - p_y2) <= dH:
                edge_info['BottomAligned'] = True
                edge_info['yError'] = calcError(c_y2, p_y2, dH)
            elif abs(cy - py) <= dH:
                edge_info['Middle'] = True
                edge_info['yError'] = calcError(cy, py, dH)
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
            contains_edge_info[(parent, node)] = populate_contain_alignments(parent, node, loc)
    return cMap


def populate_sibling_properties(node1, node2, loc):
    deltaH = 5
    deltaW = 5
    edge_info = {'LeftEdgeAligned': False,
                 'RightEdgeAligned': False,
                 'TopEdgeAligned': False,
                 'BottomEdgeAligned': False,
                 'LeftRight': False,
                 'RightLeft': False,
                 'TopBottom': False,
                 'BottomTop': False,
                 'TBDiff': 0,
                 'BTDiff': 0,
                 'RLDiff': 0,
                 'LRDiff': 0
                 }
    node1_x1 = loc[node1]['x']
    node1_x2 = loc[node1]['x'] + loc[node1]['width']
    node1_y1 = loc[node1]['y']
    node1_y2 = loc[node1]['y'] + loc[node1]['height']

    node2_x1 = loc[node2]['x']
    node2_x2 = loc[node2]['x'] + loc[node2]['width']
    node2_y1 = loc[node2]['y']
    node2_y2 = loc[node2]['y'] + loc[node2]['height']

    edge_info['TBDiff'] = abs(node1_y1 - node2_y2)
    edge_info['BTDiff'] = abs(node1_y2 - node2_y1)
    edge_info['LRDiff'] = abs(node1_x2 - node2_x1)
    edge_info['RLDiff'] = abs(node1_x1 - node2_x2)

    if abs(node1_x1 - node2_x1) <= deltaW:
        edge_info['LeftEdgeAligned'] = True

    if abs(node1_x2 - node2_x2) <= deltaW:
        edge_info['RightEdgeAligned'] = True

    if abs(node1_y1 - node2_y1) <= deltaH:
        edge_info['TopEdgeAligned'] = True

    if abs(node1_y2 - node2_y2) <= deltaH:
        edge_info['BottomEdgeAligned'] = True

    if node1_x2 < node2_x1:
        edge_info['LeftRight'] = True

    if node2_x2 < node1_x1:
        edge_info['RightLeft'] = True

    if node1_y2 < node2_y1:
        edge_info['TopBottom'] = True

    if node2_y2 < node1_y1:
        edge_info['BottomTop'] = True

    return edge_info


def populate_sibling_edges(cMap, loc, siblings_edge_info):
    for value in cMap.values():
        siblings = value[:]
        while len(siblings) > 0:
            node = siblings[0]
            siblings.pop(0)

            for n in siblings:
                siblings_edge_info[(node, n)] = populate_sibling_properties(node, n, loc)
                siblings_edge_info[(n, node)] = populate_sibling_properties(n, node, loc)


def get_parent(c, cMap):
    for parent, children in cMap.items():
        for child in children:
            if child == c:
                return parent
    return None


def testSizeDiff(p1, p2, e1, e2):
    if p1 ^ p2:
        if p1 and e1 < 0.8:
            return True
        if p2 and e2 < 0.8:
            return True
    return False


def isSignificantDiff(a, b):
    diffThreshold = 5
    if abs(a - b) > diffThreshold:
        return True
    return False


def compare_parents(c1, c2, cMap1, cMap2, contains_edge_info1, contains_edge_info2):
    issues = []
    p1 = get_parent(c1, cMap1)
    p2 = get_parent(c2, cMap2)
    if p1 is None and p2 is None:
        return issues
    elif p1 is None and p2 is not None:
        issues.append('MISSING-PARENT-1 %s %s' % (c1, c2))
        return issues
    elif p1 is not None and p2 is None:
        issues.append('MISSING-PARENT-2 %s %s' % (c1, c2))
        return issues

    expected_p2 = matched12_xpaths[p1]
    if expected_p2 != p2:
        issues.append('PARENTS DIFFER (%s-%s) (%s-%s)' % (c1, c2, p2, expected_p2))
        return issues

    # matching SizeDiffY for both c1 and c2 as we are comparing y values in it. (different from xperts implementation)
    if contains_edge_info1[(p1, c1)]['SizeDiffY'] and contains_edge_info2[(p2, c2)]['SizeDiffY']:
        if testSizeDiff(contains_edge_info1[(p1, c1)]['TopAligned'], contains_edge_info2[(p2, c2)]['TopAligned'], contains_edge_info1[(p1, c1)]['yError'], contains_edge_info2[(p2, c2)]['yError']):
            issues.append('TOP-ALIGNMENT %s %s' % (c1, c2))
        if testSizeDiff(contains_edge_info1[(p1, c1)]['BottomAligned'], contains_edge_info2[(p2, c2)]['BottomAligned'], contains_edge_info1[(p1, c1)]['yError'], contains_edge_info2[(p2, c2)]['yError']):
            issues.append('BOTTOM-ALIGNMENT %s %s' % (c1, c2))
        if testSizeDiff(contains_edge_info1[(p1, c1)]['Middle'], contains_edge_info2[(p2, c2)]['Middle'], contains_edge_info1[(p1, c1)]['yError'], contains_edge_info2[(p2, c2)]['yError']):
            issues.append('VMID-ALIGNMENT %s %s' % (c1, c2))
        if contains_edge_info1[(p1, c1)]['vFill'] ^ contains_edge_info2[(p2, c2)]['vFill']:
            issues.append('VFILL %s %s' % (c1, c2))

    if contains_edge_info1[(p1, c1)]['SizeDiffX'] and contains_edge_info2[(p2, c2)]['SizeDiffX']:
        if testSizeDiff(contains_edge_info1[(p1, c1)]['LeftJustified'], contains_edge_info2[(p2, c2)]['LeftJustified'], contains_edge_info1[(p1, c1)]['xError'], contains_edge_info2[(p2, c2)]['xError']):
            issues.append('LEFT-JUSTIFICATION %s %s' % (c1, c2))
        if testSizeDiff(contains_edge_info1[(p1, c1)]['RightJustified'], contains_edge_info2[(p2, c2)]['RightJustified'], contains_edge_info1[(p1, c1)]['xError'], contains_edge_info2[(p2, c2)]['xError']):
            issues.append('RIGHT-JUSTIFICATION %s %s' % (c1, c2))
        if testSizeDiff(contains_edge_info1[(p1, c1)]['Centered'], contains_edge_info2[(p2, c2)]['Centered'], contains_edge_info1[(p1, c1)]['xError'], contains_edge_info2[(p2, c2)]['xError']):
            issues.append('CENTER-ALIGNMENT %s %s' % (c1, c2))
        if contains_edge_info1[(p1, c1)]['hFill'] ^ contains_edge_info2[(p2, c2)]['hFill']:
            issues.append('HFILL %s %s' % (c1, c2))

    return issues


def get_siblings(c, cMap):
    for parent, children in cMap.items():
        for child in children:
            if child == c:
                children.remove(child)
                return children[:]
    return []


def compare_siblings(c1, c2, cMap1, cMap2, siblings_edge_info1, siblings_edge_info2):
    issues = []
    s_c1 = get_siblings(c1, cMap1)
    s_c2 = get_siblings(c2, cMap2)
    matched = {}
    unmatch1 = []
    unmatch2 = []

    for s1 in s_c1:
        match = False
        for s2 in s_c2:
            if matched12_xpaths[s1] == s2:
                matched[s1] = s2
                s_c2.remove(s2)
                match = True
                break
        if match is False:
            unmatch1.append(s1)
    unmatch2 = s_c2

    for sib in unmatch1:
        issues.append('MISSING-SIBLING-1 - %s' % sib)

    for sib in unmatch2:
        issues.append('MISSING-SIBLING-2 - %s' % sib)

    for x, y in matched.items():
        if siblings_edge_info1[(c1, x)]['TopEdgeAligned'] ^ siblings_edge_info2[(c2, y)]['TopEdgeAligned']:
            issues.append('TOP-EDGE-ALIGNMENT %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['RightEdgeAligned'] ^ siblings_edge_info2[(c2, y)]['RightEdgeAligned']:
            issues.append('RIGHT-EDGE-ALIGNMENT %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['BottomEdgeAligned'] ^ siblings_edge_info2[(c2, y)]['BottomEdgeAligned']:
            issues.append('BOTTOM-EDGE-ALIGNMENT %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['LeftEdgeAligned'] ^ siblings_edge_info2[(c2, y)]['LeftEdgeAligned']:
            issues.append('LEFT-EDGE-ALIGNMENT %s - %s' % (x, y))

        if siblings_edge_info1[(c1, x)]['TopBottom'] ^ siblings_edge_info2[(c2, y)]['TopBottom'] and isSignificantDiff(siblings_edge_info1[(c1, x)]['TBDiff'], siblings_edge_info2[(c2, y)]['TBDiff']):
            issues.append('TOP-BOTTOM %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['BottomTop'] ^ siblings_edge_info2[(c2, y)]['BottomTop'] and isSignificantDiff(siblings_edge_info1[(c1, x)]['BTDiff'], siblings_edge_info2[(c2, y)]['BTDiff']):
            issues.append('BOTTOM-TOP %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['LeftRight'] ^ siblings_edge_info2[(c2, y)]['LeftRight'] and isSignificantDiff(siblings_edge_info1[(c1, x)]['LRDiff'], siblings_edge_info2[(c2, y)]['LRDiff']):
            issues.append('LEFT-RIGHT %s - %s' % (x, y))
        if siblings_edge_info1[(c1, x)]['RightLeft'] ^ siblings_edge_info2[(c2, y)]['RightLeft'] and isSignificantDiff(siblings_edge_info1[(c1, x)]['RLDiff'], siblings_edge_info2[(c2, y)]['RLDiff']):
            issues.append('RIGHT-LEFT %s - %s' % (x, y))
    return issues


# 1 -> chrome 2 -> firefox
results = []
for dom_file in dom_files:
    matched21 = {}
    matched12 = {}
    matched12_xpaths = {}
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
        print('Large number of nodes to match -- skipping\n\n')
        continue

    do_match(chrome_etree, firefox_etree)
    print('Matched Nodes (without alignment): %d' % len(matched21))

    vertices_chrome = []
    vertices_firefox = []
    for chrome_node, firefox_node in matched12.items():
        chrome_xpath = chrome_tree.getpath(chrome_node)
        firefox_xpath = firefox_tree.getpath(firefox_node)
        matched12_xpaths[chrome_xpath] = firefox_xpath

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

    chrome_siblings_edge_info = {}
    firefox_siblings_edge_info = {}
    populate_sibling_edges(chrome_cMap, chrome_loc, chrome_siblings_edge_info)
    populate_sibling_edges(firefox_cMap, firefox_loc, firefox_siblings_edge_info)

    issues = []
    total_matched_nodes = len(matched21)

    for chrome_xpath, firefox_xpath in matched12_xpaths.items():
        parent_issues = compare_parents(chrome_xpath, firefox_xpath, chrome_cMap, firefox_cMap, chrome_contains_edge_info, firefox_contains_edge_info)
        sibling_issues = compare_siblings(chrome_xpath, firefox_xpath, chrome_cMap, firefox_cMap, chrome_siblings_edge_info, firefox_siblings_edge_info)

        if len(parent_issues) or len(sibling_issues):
            total_matched_nodes -= 1
        issues.extend(parent_issues)
        issues.extend(sibling_issues)

    print('Matched Nodes (with alignment): %d\n\n' % total_matched_nodes)
    image_name = '_'.join(dom_file.split('_')[1:])

    if total_matched_nodes == min(len(chrome_nodes), len(firefox_nodes)):
        label = 'y'
    else:
        label = 'n'
    results.append([image_name, label, total_matched_nodes, len(chrome_nodes), len(firefox_nodes)])


with open('dom_test_labels.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow(['Image Name', 'Label', 'Matched Nodes', 'Chrome Nodes', 'Firefox Nodes'])
    for row in results:
        writer.writerow(row)
