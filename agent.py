import time
import json
from urlparse import urlparse
from multiprocessing.pool import ThreadPool

import mechanize
import requests as reqs

from htmlutil import *

def getBrowser():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [
        ('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
        ('Accept-Encoding', 'gzip,deflate'),
        ('Accept-Language', 'en-US,en;q=0.8,ko;q=0.6'),
        ('Cache-Control', 'max-age=0'),
        ('Connection', 'keep-alive'),
    ]
    return br

def fetchSectionList(termcode, c_subj, c_num):
    br = getBrowser()
    # open schedule
    br.open("http://wl.mypurdue.purdue.edu/schedule")
    br.form = list( br.forms() )[0]
    br['p_term'] = [termcode]
    br.submit()         
    
    # Now we are in course selection mode
    br.form = list( br.forms() )[0]
    for control in br.form.controls:
        if control.name == 'sel_subj' and control.type == 'select':
            control.value = [c_subj]
        if control.name == 'sel_crse' and control.type == 'text':
            control.value = c_num
    br.submit()
  
    # Course Schedule Listing Page
    p = urlparse(br.geturl())
    host = p.scheme + '://' + p.netloc
    html = br.response().read() 
    sections = parseSectionList(html)
    for s in sections:
        s['link'] = host + s['link']
    return sections

def parseSectionList(html):
    sections = []

    html = html.splitlines()
    tag = None
    for line in html:
        tag = tag + line if tag else line
        if 'ddheader' in tag:
            tag = None
            continue
        if isTagHeadInHTML('th', tag):
            if isTagTailInHTML('th', tag):
                if 'ddlabel' in tag:
                    section = {
                        'meetings': [],
                        'link': None,
                        'schedule_type': None
                    }
                    link = getAttrFromTag('a', 'href', tag)
                    section['link'] = link.replace('&amp;', '&')
                    count = -1
                tag = None
        elif isTagTailInHTML('td', tag):
            if isTagHeadInHTML('td', tag):
                if 'dddefault' in tag:
                    count = count+1

                    tag = tag.replace('&nbsp;', ' ')

                    if count == 0: # TYPE
                        meeting = {}
                        pass
                    elif count == 1:    # TIME
                        meeting['time'] = getTextFromTag('td', tag)
                    elif count == 2:    # DAYS
                        meeting['days'] = getTextFromTag('td', tag)
                    elif count == 3:    # WHERE
                        pass
                    elif count == 4:    # DATE RANGE
                        pass
                    elif count == 5:    # SCHEDULE TYPE
                        if section['schedule_type'] == None:
                            section['schedule_type'] = getTextFromTag('td', tag)
                    elif count == 6:    # INSTRUCTOR
                        meeting['instructor'] = getTextFromTag('td', tag)
                        section['meetings'].append(meeting)
                        if len(sections) == 0 or sections[-1] is not section:
                            sections.append(section)
                tag = None
        else:
            tag = None
    return sections 

def fetchSectionDetails(url):
    br = getBrowser()
    br.open(url)
    html = br.response().read() 
    return parseSectionDetail(html)

def parseSectionDetail(html):
    html = html.splitlines()
    tag = None
    for line in html:
        tag = tag + line if tag else line
        if 'ddheader' in tag:
            tag = None
            continue
        if isTagHeadInHTML('th', tag):
            if isTagTailInHTML('th', tag):
                if 'ddlabel' in tag:
                    title = getTextFromTag('th', tag)
                    if ' - ' in title:
                        detail = {}
                        sp = title.split(' - ')
                        detail['name'] = sp[0]
                        detail['crn'] = sp[1]
                        detail['code'] = sp[3]
                        count = -1
                tag = None
        elif isTagTailInHTML('td', tag):
            if isTagHeadInHTML('td', tag):
                if 'dddefault' in tag:
                    count = count+1

                    if count == 0: # CAPACITY
                        pass
                    elif count == 1:    # ACTUAL
                        pass
                    elif count == 2:    # REMAINING
                        detail['seats'] = int(getTextFromTag('td', tag))
                        return detail
                tag = None
        else:
            tag = None
    return None

def getSemesterCode(term):
    term = term.replace(' ','') .lower()

    sem = None
    year = None
    err_sem = Exception('Invalid term semester %s' % term)
    err_year = Exception('Invalid term year %s' % term)

    for i, c in enumerate(term):
        if i == 0:
            continue
        if term[0].isdigit() != c.isdigit():
            a, b = term[:i], term[i:]
            sem, year = (a, b) if c.isdigit() else (b, a)
            break

    for c in sem:
        if not c.isalpha():
            raise err_sem
    for c in year:
        if not c.isdigit():
            raise err_year
    
    sem_codes = {
        'fall': '10',
        'spring': '20',
        'summer': '30',
    }
    if sem not in sem_codes:
        raise err_sem
    if sem == 'fall':
        year = str(int(year) + 1)
    termcode = year + sem_codes[sem]
    return termcode
     
def normalizeInput(coursename):
    coursename = coursename.replace(' ','') .upper()

    subj = None
    num = None
    err_subj = Exception('Invalid course subject: %s' % coursename)
    err_num = Exception('Invalid course number: %s' % coursename)

    for i, c in enumerate(coursename):
        if c.isdigit():
            subj = coursename[:i]
            num = coursename[i:]
            break

    if subj == None:
        raise err_subj
    if num == None:
        raise err_num

    if len(num) == 3:
        num += '00'
    if not len(num) == 5:
        raise err_subj
    if not len(subj) <= 4:
        raise err_num

    common = {'BIO':'BIOL', 'ENG':'ENGL'}
    if subj in common:
        subj = common[subj]

    for c in subj:
        if not c.isalpha():
            raise err_subj
    for c in num:
        if not c.isdigit():
            raise err_num
    return (subj, num)


def getCourseInfo(term, coursename):
    termcode = getSemesterCode(term)
    c_subj, c_num = normalizeInput(coursename)

    sections = fetchSectionList(termcode, c_subj, c_num)
    
    # visit links and get seats/waitlist seats
    links = [x['link'] for x in sections]
    pool = ThreadPool(8)
    asyncs = []
    # print fetchSectionDetails(links[0])
    for link in links:
        a = pool.apply_async(fetchSectionDetails, [link])
        asyncs.append(a)

    details = []
    for a in asyncs:
        v = a.get()
        if v:
            details.append(v)
    
    # merge section dic with seat_all into ret_all
    r = { 'Course': c_subj + c_num + ' ' + details[0]['name'] }
    for section, detail in zip(sections, details):
        stype = section['schedule_type']
        if stype not in r:
            r[stype] = {}
        d = dict(section)
        d['code'] = detail['code']
        d['seats'] = detail['seats']
        r[stype][detail['crn']] = d
    return r


if __name__ == '__main__':
    import time
    start = time.clock()
    import sys
    course = sys.argv[1]
    if len(sys.argv) > 3:
        term = sys.argv[2] + sys.argv[3]
    else:
        term = 'fall 2015'
    info = getCourseInfo(term, course)
    print '\n\n\n', json.dumps(info).replace('{', '\n').replace('}', '\n')
    print "global: " + str(time.clock() - start)


