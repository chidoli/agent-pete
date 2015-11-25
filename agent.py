import requests
from requests.compat import urljoin
from bs4 import BeautifulSoup

URL_BASE = "https://selfservice.mypurdue.purdue.edu/prod/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=%s"

class Agent:
  headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}

  def __init__(self, sid, server, term, crn):
    self.sid = sid
    self.server = server
    self.term = term
    self.crn = crn

  def get_html(self, url):
    resp = requests.get(url, headers=self.headers)
    return resp.content

  def parse(self, html):
    soup = BeautifulSoup(html, 'html.parser')
    capacity = int(soup.select('tr td[class~=dddefault]')[1].text)
    remaining = int(soup.select('tr td[class~=dddefault]')[3].text)
    return remaining, capacity

  def report(self, remaining, capacity):
    url = urljoin(self.server, 'report')
    data = {
      'sid': self.sid,
      'term': self.term,
      'crn': self.crn,
      'remaining': remaining,
      'capacity': capacity
    }
    resp = requests.post(url, data=data)
    notis = resp.json()['notifications']
    print notis

  def run(self):
    url = URL_BASE % (self.term, self.crn)
    html = self.get_html(url)
    rem, cap = self.parse(html)
    self.report(rem, cap)


if __name__ == '__main__':
  POOL_SIZE = 20
  REQUEST_COUNT = 100

  sid = '0'
  server = ''
  term = '201620'
  crns = ['10646', '12888', '14429', '12879', '12877', '14428']
  cnt = len(crns)
  crns = [crns[i % cnt] for i in xrange(REQUEST_COUNT)]

  def report(self, rem, cap):
    print '[crn %s] %d / %d' % (self.crn, rem, cap)
  Agent.report = report

  def spawn(crn):
    return Agent(sid, server, term, crn).run()
    
  from multiprocessing import Pool
  res = Pool(POOL_SIZE).map(spawn, crns)
  
  print 'Pool size: %d' % POOL_SIZE
  print 'CRNs: %d' % len(crns)
