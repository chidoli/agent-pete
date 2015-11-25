from subprocess import Popen, PIPE
from email.mime.text import MIMEText

def sendmail(sender, receiver, subject, content):
  cmd = ['sendmail', '-t']
  p = Popen(cmd, stdin=PIPE)

  msg = MIMEText(content, 'html')
  msg['From'] = sender
  msg['To'] = receiver
  msg['Subject'] = subject
  msg['Content-Type'] = 'text/html'

  p.stdin.write(msg.as_string())
  res = p.communicate()[0]

