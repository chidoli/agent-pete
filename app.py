import smtplib
from email.mime.text import MIMEText
import json

from agent import getCourseInfo
from config import conf, load_conf
from util import now_str


def sendmail(sender, receiver, subject, body):
    msg = MIMEText(body, 'html')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject

    smtp = conf['smtp']
    s = smtplib.SMTP(smtp['server'], smtp['port'])
    s.starttls()
    s.login(smtp['id'], smtp['pw'])
    s.sendmail(sender, [receiver], msg.as_string())
    s.quit()

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        load_conf(sys.argv[1])
    else:
        raise Exception('Configuration file needed. (ex. default.conf)')
    if conf['smtp']['pw'] == '':
        raise Exception('SMTP password is not configured')

    sender = conf['sys']['sender']

    for req in conf['requests']:
        receiver = req['requester']
        course = req['course']

        info = getCourseInfo(course)
        available = False
        body = ''
        
        body += '<h4>%s</h4>\n' % info['Course']
        body += '<table>\n'
        for k, v in info.items():
            if k == 'Course':
                continue
            for crn, _v in v.items():
                body += '<tr>\n'
                body += '<td>%s</td>\n' % k
                body += '<td><b>%s</b></td>\n' % crn 
                val = [_v['sec'], _v['days'][0], _v['time'][0], _v['inst'][0]]
                body += '\n'.join([('<td>%s</td>' % x) for x in val]) + '\n'
                body += '<td><b>%s</b></td>\n' % _v['seats']
                body += '</tr>\n'
                if _v['seats'] > 0:
                    sec = _v['sec']
                    if 'section' in req:
                        valid = False
                        for rsec in req['section']:
                            if sec == rsec:
                                valid = True
                                break
                        if not valid:
                            continue
                    available = True
        body += '</table>\n'
        url = 'mypurdue.purdue.edu'
        body += '\n<a href="http://%s">%s</a>\n' % (url, url)

        if available:
            now = now_str('%H:%M:%S')
            subject = '%s available at %s'
            subject = subject % (course, now)
            body = '%s\n\n\n%s' % (subject, body)
            body = '<html>\n%s\n</html>\n' % body
            
            sendmail(sender, receiver, subject, body)
        print '\n\n\n', json.dumps(info)
