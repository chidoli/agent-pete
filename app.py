from flask import Flask, json, request
from flask.ext.sqlalchemy import SQLAlchemy

import time

DEBUG = True

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./agent_pete.db'
db = SQLAlchemy(app)

class Section(db.Model):
  term = db.Column(db.String(6), primary_key=True)
  crn = db.Column(db.String(6), primary_key=True)
  coursename = db.Column(db.Text)
  remaining = db.Column(db.Integer)
  capacity = db.Column(db.Integer)
  last_reported_spawn = db.Column(db.Text)

  def __init__(self, term, crn, coursename):
    self.term = term
    self.crn = crn
    self.coursename = coursename

  def __repr__(self):
    return '<Secion: %r>' % self.dict()

  def dict(self):
    return {
      'term': self.term,
      'crn': self.crn,
      'coursename': self.coursename,
      'remaining': self.remaining,
      'capacity': self.capacity,
      'last_reported_spawn': self.last_reported_spawn
    }


class User(db.Model):
  username = db.Column(db.String(32), primary_key=True)

  def __init__(self, username):
    self.username = username

  def __repr__(self):
    return '<User: %r>' % self.dict()

  def dict(self):
    return {
      'username': self.username
    }


class Request(db.Model):
  rid = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(32), db.ForeignKey('user.username'))
  term = db.Column(db.String(6), db.ForeignKey('section.term'))
  crn = db.Column(db.String(6), db.ForeignKey('section.crn'))

  user = db.relationship('User',
          backref=db.backref('requests', lazy='dynamic'))
  section = db.relationship('Section',
          primaryjoin="and_(Section.term==Request.term, Section.crn==Request.crn)",
          backref=db.backref('requests', lazy='dynamic'))

  def __init__(self, username, term, crn):
    self.username = username
    self.term = term
    self.crn = crn

  def __repr__(self):
    return '<Request: %r>' % self.dict()

  def dict(self):
    return {
      'rid': self.rid,
      'username': self.username,
      'term': self.term,
      'crn': self.crn
    }


def to_dict(lst):
  return map(lambda x: x.dict(), lst)


@app.route('/init')
def route_init():
  if app.debug == True:
    db.drop_all()
    db.create_all()

    db.session.add(Section('201620', '10646', 'AGR20100'))
    db.session.add(Section('201620', '12888', 'CS11000'))
    db.session.add(Section('201620', '14429', 'CS11000'))
    db.session.add(Section('201620', '12879', 'CS11000'))
    db.session.add(Section('201620', '12877', 'CS11000'))
    db.session.add(Section('201620', '14428', 'CS11000'))

    db.session.add(User('lim8'))
    db.session.add(User('choi257'))

    db.session.add(Request('lim8', '201620', '10646'))
    db.session.add(Request('lim8', '201620', '12888'))
    db.session.add(Request('choi257', '201620', '12888'))
    db.session.add(Request('choi257', '201620', '14429'))

    db.session.commit()
  return "Initialized"

@app.route('/sections')
def route_sections():
  secs = Section.query.all()
  return json.jsonify(sections=to_dict(secs))

@app.route('/requests')
def route_requests():
  reqs = Request.query.all()
  return json.jsonify(requests=to_dict(reqs))

@app.route('/user/<username>')
def route_user(username):
  u = User.query.filter_by(username=username).first()
  reqs = u.requests.all()
  return json.jsonify(user=u.dict(), requests=to_dict(reqs))

@app.route('/report', methods=['POST'])
def route_report():
  spawn_id = request.form['sid']
  term = request.form['term']
  crn = request.form['crn']
  remaining = request.form['remaining']
  capacity = request.form['capacity']

  s = Section.query.filter_by(term=term, crn=crn).first()
  s.remaining = remaining
  s.capacity = capacity
  s.last_reported_spawn = spawn_id

  db.session.add(s)
  db.session.commit()

  notis = []
  for r in s.requests.all():
    d = s.dict()
    del d['last_reported_spawn']

    notis.append({
      'username': r.username,
      'sections': [d]
    })
  
  return json.jsonify(notifications=notis)


if __name__ == '__main__':
  import sys
  port = int(sys.argv[1]) if len(sys.argv) == 2 else 8257

  app.debug = DEBUG
  app.run(host='0.0.0.0', port=port)
