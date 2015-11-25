import requests
from requests.compat import urljoin

from agent import Agent
    
from multiprocessing import Pool

def spawn(request):
  Agent(request['sid'], request['term'], request['crn']).run()

class Spawner:
  def __init__(self, server, pool_size):
    self.server = server
    self.pool_size = pool_size

  def get_requests(self):
    url = urljoin(self.server, 'requests')
    resp = requests.get(url)
    return resp.json().get('requests')

  def run(self, spawn_id):
    reqs = self.get_requests()
    for r in reqs:
      r['sid'] = spawn_id
    Pool(self.pool_size).map(spawn, reqs)


if __name__ == '__main__':
  def report(self, rem, cap):
    print {
      'sid': self.sid,
      'crn': self.crn,
      'remaining': rem,
      'capacity': cap
    }
  Agent.report = report

  import time
  spawn_id = str(time.time())
  Spawner('http://0.0.0.0:8000', 5).run(spawn_id)
