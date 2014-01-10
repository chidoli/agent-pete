#!/usr/bin/python

import mechanize
import threading
import time
import copy
from HTMLParser import HTMLParser


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
                count = (count+1)%7
            if( count == 0 ): # TYPE
                continue
            elif( count == 1):    # TIME
                temp['time'].append( strip_tags( html[i] ))
            elif( count == 2):    # DAYS
                temp['days'].append( strip_tags( html[i] ))
            elif( count == 3):    # WHERE
                continue
            elif( count == 4):    # DATE RANGE
                continue
            elif( count == 5):    # Schedule Type
                temp['stype'].append( strip_tags( html[i] ))
            elif( count == 6):    # Instructor
                temp['inst'].append( strip_tags( html[i] ))
                attrs.append( copy.copy(temp) )
    return attrs
    

seat_all = []

def getSeats(html):
    seats =[]
    html = html.split('\n')

    for line in html:
        if 'dddefault' in line and len(line) < 32: # arbitrary
           seats.append( strip_tags(line) ) 

    return seats[3] # third entry of this page gives the num of available seats
 


# Link Thread returns the following thread
# [ <course section>, <course crn> , <seat>, <course name> ]
class linkThread(threading.Thread):
  def __init__(self, index, br, link):
      threading.Thread.__init__(self)
      self.index = index
      self.br = br
      self.link = link

  def run(self):
      self.br.follow_link(self.link)
      html = self.br.response().read()

      #print "thread " + str(self.index) + " launched.."
      global seat_all
      seat_current = []
      
      # get section number here
      course_raw = self.link.text
      course_split = course_raw.split(" -");
      course_section = course_split[3]
      course_section = course_section[1:len(course_section)]
      seat_current.append(course_section)

      # get crn
      course_crn = course_split[1];
      seat_current.append(course_crn)

      # get seat info here
      seat_current.append(getSeats(html))

      # get course name
      seat_current.append( course_split[0] )

      # commit
      seat_all[self.index] = seat_current
      html = self.br.response().read()

def normalizeInput(coursename):
    # conver to lower case and classify
    coursename = coursename.upper();        # convert to lower
    coursename = coursename.replace(' ','') # remove spaces

    # find the division between <coursedept><coursenum>
    index = 0
    for char in coursename:
        if char.isdigit():
            break 
        index += 1

    # check 1: course number must be 3 or 5
    if ( (coursename.__len__() - index) != 3 ) and ( (coursename.__len__() - index) != 5 ) :
        return None

    # check 2: dept name must be less than 4 chars long
    if index > 4 :
        return None

    # we should add 00 at the end if the course number length == 3
    if ( (coursename.__len__() - index) == 3): 
        coursename = coursename + "00"

        # common mistakes 1: people write bio instead of biol
        if coursename[0] == "BIO":
            newInput = ("BIOL", coursename[0])
            coursename = newInput

    return (coursename[0:index], coursename[index:coursename.__len__()])


def crawlPurdue(coursename):
    """
    Returns a dictionary of all sections with following information:
    section number, section type, section time, section days
    section availability, section instructor
    """

    # Normalize Input
    coursename = normalizeInput(coursename)

    if coursename == None:
      #print "err: bad coursename"
      return None

    br = mechanize.Browser()
    # set some headers
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Firefox')]

    # open schedule
    br.open("http://wl.mypurdue.purdue.edu/schedule")
  
    # select form
    br.form = list( br.forms() )[0]
    # 201410 = fall 2014, 201420 = Spring, 201430 = summer
    br['p_term'] = ['201420']
  
    # submit the form
    br.submit()         
    
    #print br.response().read()
  
    # Now we are in course selection mode
    br.form = list( br.forms() )[0]
    try :
        for control in br.form.controls:
            if control.name == 'sel_subj' and control.type == 'select':
              control.value = [coursename[0]]
            if control.name == 'sel_crse' and control.type == 'text':
              control.value = coursename[1]
    except:
        import sys
        e = sys.exc_info()[0] 
        return None

    br.submit()
  
  
    # We are now in Course Schedule Listing Page
    html = br.response().read() 
    section_all = getAttr(html)
   
    #print attr_all
    # now we need to find the link to the course
    links = []
  
    for link in br.links():
        if link.text is None:
            continue
        if coursename[0] in link.text and coursename[1] in link.text:
            # all the follwing links must be of some value
            links.append(link)
  
    if not links:
        #print "course not found"
        return None
  
    # visit links and get seats/waitlist seats
    global seat_all
    seat_all_len = len(links)
    seat_all = [None for x in xrange(seat_all_len)]
    threads = [None for x in xrange(seat_all_len)]

    i = 0
    for link in links:
        threads[i] = linkThread( i, copy.copy(br), link  )
        threads[i].start()
        i += 1
    
    # wait for all threads to complete
    for thread in threads:
        thread.join()

    # merge section dic with seat_all into ret_all
    ret_all = {
        'Course': coursename[0] + coursename[1] + " " + seat_all[0][3],
    }
    for seat, section in zip(seat_all, section_all):
        stype = section['stype'][0]
        if stype not in ret_all:
            ret_all[stype] = {}
        ret_all[stype][seat[1]] = {
            'time': section['time'], 
            'sec': seat[0],
            'inst': section['inst'], 
            'days': section['days'],  
            'seat': seat[2]
        }
    return ret_all

def getCourseInfo(arg):
    ret = crawlPurdue(arg)
    return ret
  
  
if __name__ == '__main__':
   start = time.clock()
   import sys
   info = getCourseInfo(sys.argv[1])
   print '\n\n\n', info
   print "global: " + str(time.clock() - start)
  

