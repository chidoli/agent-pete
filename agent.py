#!/usr/bin/python

import json
import time
import copy
from multiprocessing.pool import ThreadPool
from HTMLParser import HTMLParser

import mechanize


class MyHTMLParser(HTMLParser):
    # option: enable parsing data
    def __init__(self, option=0):
        HTMLParser.__init__(self)
        self.tables = []
        self.start = -1
        self.option = option
        if option == 1:
            self.fed = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if attrs[0][1] == 'datadisplaytable' and len(attrs) == 2:
                self.start=self.getpos()[0] # mark the start of table
    def handle_endtag(self, tag):
        # mark the end of table only if the start of table has been marked
        if tag == 'table' and self.start != -1:
            self.tables.append( (self.start, self.getpos()[0]) )
            self.start = -1
    
    def handle_data(self, d):
        if self.option == 1:
            self.fed.append(d)
    
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MyHTMLParser(1)
    s.feed(html)
    return s.get_data()


def getAttr(html):
    attrs =[]
    parser = MyHTMLParser()
    parser.feed(html)
    
    html = html.splitlines()
    for j in range(0, len(parser.tables) ):
        count = -1;
        temp = { 'time': [], 'days': [], 'stype': [], 'inst': []}
        for i in range (parser.tables[j][0], parser.tables[j][1]):
            if 'dddefault' in html[i]:
                count = count+1
            if count == 0: # TYPE
                continue
            elif count == 1:    # TIME
                temp['time'].append(strip_tags( html[i] ))
            elif count == 2:    # DAYS
                temp['days'].append(strip_tags( html[i] ))
            elif count == 3:    # WHERE
                continue
            elif count == 4:    # DATE RANGE
                continue
            elif count == 5:    # Schedule Type
                temp['stype'].append(strip_tags( html[i] ))
            elif count == 6:    # Instructor
                temp['inst'].append(strip_tags( html[i] ))
                attrs.append( copy.copy(temp) )
                count = -1
    return attrs


def getSeats(html):
    seats =[]
    html = html.split('\n')
    
    for line in html:
        if 'dddefault' in line and len(line) < 32: # arbitrary
            seats.append( strip_tags(line) )
    
    return seats[3] # third entry of this page gives the num of available seats


def fetchLink(br, link):
    br.follow_link(link)
    html = br.response().read()
    
    seat = []
    
    # get section number here
    course_raw = link.text
    course_split = course_raw.split(" -");
    course_section = course_split[3]
    course_section = course_section[1:len(course_section)]
    seat.append(course_section)
    
    # get crn
    course_crn = course_split[1];
    seat.append(course_crn)
    
    # get seat info here
    seat.append(getSeats(html))
    
    # get course name
    seat.append( course_split[0] )
    
    return seat

def normalizeInput(coursename):
    coursename = coursename.upper();
    coursename = coursename.replace(' ','')
    
    subj = None
    num = None
    for i, c in enumerate(coursename):
        if c.isdigit():
            subj = coursename[:i]
            num = coursename[i:]
            break
    
    if len(num) == 3:
        num += '00'
    if not len(num) == 5:
        raise Exception('Invalid course number: %s' % (coursename))
    
    if not len(subj) <= 4:
        raise Exception('Invalid course subject: %s' % (coursename))
    
    if subj == 'BIO':
        subj = 'BIOL'
    
    return (subj, num)


def getCourseInfo(coursename):
    c_subj, c_num = normalizeInput(coursename)
    
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]
    
    # open schedule
    br.open("http://wl.mypurdue.purdue.edu/schedule")
    br.form = list( br.forms() )[0]
    # 201410 = fall 2014, 201420 = Spring, 201430 = summer
    br['p_term'] = ['201420']
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
    html = br.response().read()
    sections = getAttr(html)
    
    # now we need to find the link to the course
    links = []
    for link in br.links():
        if link.text is None:
            continue
        if c_subj in link.text and c_num in link.text:
            # all the follwing links must be of some value
            links.append(link)
    
    if not links:
        raise Exception('Course %s is not found' % (coursename))
    
    # visit links and get seats/waitlist seats
    asyncs = []
    pool = ThreadPool(30)
    for link in links:
        a = pool.apply_async(fetchLink, [copy.copy(br), link])
        asyncs.append(a)
    
    seats = []
    for a in asyncs:
        v = a.get()
        if v:
            seats.append(v)
    
    # merge section dic with seat_all into ret_all
    ret_all = {
        'Course': c_subj + c_num + ' ' + seats[0][3],
    }
    for seat, section in zip(seats, sections):
        stype = section['stype'][0]
        if stype not in ret_all:
            ret_all[stype] = {}
        ret_all[stype][seat[1]] = {
            'time': section['time'],
            'sec': seat[0],
            'inst': section['inst'],
            'days': section['days'],
            'seats': int(seat[2]),
        }
    return ret_all


if __name__ == '__main__':
    start = time.clock()
    import sys
    info = getCourseInfo(sys.argv[1])
    print '\n\n\n', json.dumps(info)
    print "global: " + str(time.clock() - start)


