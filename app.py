import smtplib
from email.mime.text import MIMEText
import json

from agent import getCourseInfo
from config import conf, load_conf
from util import now_str


def sendmail(sender, receiver, subject, content):
    msg = MIMEText(content, 'html')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject

    smtp = conf['smtp']
    s = smtplib.SMTP(smtp['server'], smtp['port'])
    s.starttls()
    s.login(smtp['id'], smtp['pw'])
    s.sendmail(sender, [receiver], msg.as_string())
    s.quit()

def trsForSection(crstype, crn, code, seats, m, first_m):
    body = ''
    if first_m:
        body += '<tr>\n'
        body += '<td>%s</td>\n' % crstype
        body += '<td><b>%s</b></td>\n' % crn 
    else:
        body += '<tr>\n<td></td>\n<td></td>\n'
    mv = [ code, m['days'], m['time'], m['instructor'] ]
    body += '\n'.join([('<td>%s</td>' % x) for x in mv]) + '\n'
    if first_m:
        body += '<td><b>%s</b></td>\n' % seats
    else:
        body += '<td></td>\n'
    body += '</tr>\n'
    return body

def main():
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
        if 'term' in req:
            term = req['term']
        else:
            term = conf['sys']['term']
        info = getCourseInfo(term, course)
        availables = []

        body = ''
        for k, v in info.items():
            if k == 'Course':
                continue
            for crn, sec in v.items():
                first_m = True
                code = sec['code']
                seats = sec['seats']
                for m in sec['meetings']:
                    body += trsForSection(k, crn, code, seats, m, first_m)
                    if seats > 0:
                        if 'section' in req:
                            for s in req['section']:
                                valid = code in s
                                if valid:
                                    break
                        else:
                            valid = True
                        if valid:
                            availables.append([k, crn, code, seats, m, first_m])
                    first_m = False
        
        if 'section' in req:
            for s in req['section']:
                all_in = True
                for _s in s:
                    codes = [x[2] for x in availables]
                    if _s not in codes:
                        all_in = False
                        break
                if not all_in:
                    for _s in s:
                        if _s in codes:
                            availables.pop(codes.index(_s))

        title = '<h4>%s</h4>\n' % info['Course']
        body = '%s\n<table>\n%s</table>\n' % (title, body)
        url = 'mypurdue.purdue.edu'
        body += '\n\n\n<a href="http://%s">%s</a>\n' % (url, url)

        if len(availables) > 0:
            hl = ''
            for crstype, crn, code, seats, m, first_m in availables:
                hl += trsForSection(crstype, crn, code, seats, m, first_m)
            title = '<h4>Available Courses</h4>\n'
            hl = '%s\n<table>\n%s</table>\n' % (title, hl)
                
            now = now_str('%H:%M:%S')
            subject = '%s is available as of %s'
            subject = subject % (course, now)
            body = '<h3>%s</h3>\n\n\n%s\n%s' % (subject, hl, body)
            content = '<html>\n%s\n</html>\n' % body
            
            sendmail(sender, receiver, subject, content)
            print '\n', 'email sent to %s' % receiver
        print '\n', json.dumps(info)


if __name__ == '__main__':
    main()
