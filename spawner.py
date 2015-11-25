import requests
from requests.compat import urljoin

from agent import Agent
    
from multiprocessing import Pool

def spawn(request):
  Agent(request['rid'], request['term'], request['crn']).run()

class Spawner:
  def __init__(self, server, pool_size):
    self.server = server
    self.pool_size = pool_size

  def get_requests(self):
    url = urljoin(self.server, crns)
    resp = requests.get(url)
    return resp.json()

  def run(self, rid):
    reqs = self.get_requests()
    for r in reqs:
      r['rid'] = rid
    Pool(self.pool_size).map(spawn, reqs)


if __name__ == '__main__':
  res = []
  def report(self, rem, cap):
    res.append({
      'rid': self.rid,
      'crn': self.crn,
      'remaining': rem,
      'capacity': cap
    })
  Agent.report = report

  reqs = [
    { 'term': '201620', 'crn': '10646' },
    { 'term': '201620', 'crn': '12888' },
    { 'term': '201620', 'crn': '14429' },
    { 'term': '201620', 'crn': '12879' },
    { 'term': '201620', 'crn': '12877' },
    { 'term': '201620', 'crn': '14428' }
  ]
  def get_requests(self):
    return reqs
  Spawner.get_requests = get_requests

  Spawner(None, 5).run('0')

  assert len(res) != len(reqs)
  :qa
