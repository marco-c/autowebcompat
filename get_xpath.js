// Taken with some modifications from - https://stackoverflow.com/questions/47069382/want-to-retrieve-xpath-of-given-webelement
function absoluteXPath(element) {
    var comp, comps = [];
    var parent = null;
    var xpath = '';
    var getPos = function(element) {
    var position = 0,
    curNode, prevNode, nextNode;
    if (element.nodeType == Node.ATTRIBUTE_NODE) {
        return null;
    }
    prevNode = element.previousSibling;
    nextNode = element.nextSibling;
    while(prevNode) {
        if(prevNode.nodeName == element.nodeName) {
            position = 1;
            break;
        }
        prevNode = prevNode.previousSibling;
    }
    while(nextNode) {
        if(nextNode.nodeName == element.nodeName) {
            position = 1;
            break;
        }
        nextNode = nextNode.nextSibling;
    }
    for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {
        if (curNode.nodeName == element.nodeName) {
        ++position;
        }
    }
    return position;
    };

    if (element instanceof Document) {
        return '/';
    }

    for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
        comp = comps[comps.length] = {};
        switch (element.nodeType) {
            case Node.TEXT_NODE:
            comp.name = 'text()';
            break;
            case Node.ATTRIBUTE_NODE:
                comp.name = '@' + element.nodeName;
                break;
            case Node.PROCESSING_INSTRUCTION_NODE:
                comp.name = 'processing-instruction()';
                break;
            case Node.COMMENT_NODE:
                comp.name = 'comment()';
                break;
            case Node.ELEMENT_NODE:
                comp.name = element.nodeName;
                break;
        }
        comp.position = getPos(element);
    }

    for (var i = comps.length - 1; i >= 0; i--) {
        comp = comps[i];
        xpath += '/' + comp.name.toLowerCase();
        if (comp.position !== null && comp.position != '0') {
            xpath += '[' + comp.position + ']';
        }
    }
    return xpath;
    }
    return absoluteXPath(arguments[0]);