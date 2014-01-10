#!/usr/bin/python

import json
from multiprocessing.pool import ThreadPool
from urlparse import urlparse

import mechanize
import requests as reqs
from BeautifulSoup import BeautifulSoup as Soup

from soupselect import select


def fetchSectionList(termcode, c_subj, c_num):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]

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
    schedules = []

    soup = Soup(html)
    s_tables = select(soup, 'table.datadisplaytable')
    for s_table in s_tables:
        s_subtables = select(s_table, 'table.datadisplaytable')
        s_ths = select(s_table, 'th.ddlabel')
        for s_subtable, s_th in zip(s_subtables, s_ths):
            s_tds = select(s_subtable, 'td.dddefault')
            d = {}
            keys = ['type', 'time', 'days', 'where', 'date_range', 
                    'schedule_type', 'instructors']
            for key, s_td in zip(keys, s_tds):
                d[key] = s_td.text
            schedules.append(d)

            s_anchors = select(s_th, 'a')
            d['link'] = s_anchors[0].get('href')
    return schedules 

def fetchSectionDetails(url):
    resp = reqs.get(url)
    html = resp.content
    return parseSectionDetail(html)

def parseSectionDetail(html):
    detail = {}
    soup = Soup(html)
    s_title = select(soup, 'th.ddlabel')[0]
    title_txt = s_title.text
    sp = title_txt.split(" - ");
    detail['name'] = sp[0]
    detail['crn'] = sp[1]
    detail['code'] = sp[3]

    s_subtable = select(soup, '.datadisplaytable .datadisplaytable')[0]
    s_remaining = select(s_subtable, '.dddefault')[2]
    detail['seats'] = s_remaining.text
    return detail

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
    pool = ThreadPool()
    asyncs = []
    for link in links:
        a = pool.apply_async(fetchSectionDetails, [link])
        asyncs.append(a)

    details = []
    for a in asyncs:
        v = a.get()
        if v:
            details.append(v)
        asyncs.remove(a)

    # merge section dic with seat_all into ret_all
    r = {
        'Course': c_subj + c_num + ' ' + details[0]['name'],
    }
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
   term = 'spring 2014'
   info = getCourseInfo(term, course)
   print '\n\n\n', info
   print "global: " + str(time.clock() - start)
  

