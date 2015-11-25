from flask import Flask, json
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./agent_pete.db'
db = SQLAlchemy(app)

class Section(db.Model):
  crn = db.Column(db.String(6), primary_key=True)
  term = db.Column(db.String(6), primary_key=True)
  coursename = db.Column(db.Text)
  
  def __init__(self, term, crn, coursename):
    self.term = term
    self.crn = crn
    self.coursename = coursename

  def __repr__(self):
    return '<Secion %r / %r / %r>' % (self.coursename, self.term, self.crn)


class User(db.Model):
  username = db.Column(db.String(32), primary_key=True)

  def __init__(self, username):
    self.username = username

  def __repr__(self):
    return '<User %r>' % self.username


class Request(db.Model):
  rid = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(32))
  term = db.Column(db.String(6))
  crn = db.Column(db.String(6))

  def __init__(self, username, term, crn):
    self.username = username
    self.term = term
    self.crn = crn

  def __repr__(self):
    return '<Request %r / %r / %r / %r>' % (self.rid, self.username, self.term, self.crn)


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

@app.route('/requests')
def route_requests():
  reqs = [{ 'term': r.term, 'crn': r.crn } for r in Request.query.all()]
  return json.jsonify(requests=reqs)


if __name__ == '__main__':
  app.debug = True

  app.run(host='0.0.0.0', port=8000)
