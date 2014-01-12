import re


def getTextFromTag(tagname, html):
    rstr = r'<' + tagname + r'[^>]*>((?!<\/).*)</' + tagname + r'[^>]*>'
    search = re.search(rstr, html, re.I)
    if search == None:
        return ''
    text = search.group(1)

    text = re.sub(r'<[^>]*>', '', text)
    text = text.strip()
    return text

def getAttrFromTag(tagname, attrname, html):
    _rstr = r'((?:[\']([^\']*)[\']|["]([^"]*)["]|([^ ]*)))'
    rstr = r'<' + tagname + r' ' + attrname + r'=' + _rstr + r'[^>]*>'
    search = re.search(rstr, html, re.I)
    if search == None:
        return ''
    text = search.group(1)
    text = re.sub(r'[\'\"]', r'', text)
    text = text.strip()
    return text


def isTagHeadInHTML(tagname, html):
    rstr = r'<' + tagname + r'[^>]*>'
    search = re.search(rstr, html, re.I)
    return search != None


def isTagTailInHTML(tagname, html):
    rstr = r'</' + tagname + r'[^>]*>'
    search = re.search(rstr, html, re.I)
    return search != None
