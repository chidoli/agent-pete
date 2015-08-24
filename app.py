from email.mime.text import MIMEText
import json

from agent import getCourseInfo
from config import conf, load_conf
from util import now_str

from subprocess import Popen, PIPE


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
    # print res

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
                        if 'crns' in req:
                            for c in req['crns']:
                                valid = crn in c
                                if valid:
                                    break
                        else:
                            valid = True
                        if valid:
                            availables.append([k, crn, code, seats, m, first_m])
                    first_m = False
        
        if 'crns' in req:
            for crns in req['crns']:
                all_in = True
                avaCrns = [x[2] for x in availables]
                for crn in crns:
                    if crn not in avaCrns:
                        all_in = False
                        break
                if not all_in:
                    idxs = []
                    for crn in crns:
                        if crn in avaCrns:
                            idxs.append(avaCrns.index(crn))
                    
                    new_availables = []
                    for i in xrange(len(availables)):
                        if i not in idxs:
                            new_availables.append(availables.get(i))
                    availables = new_availables
                        
        if len(availables) > 0:
            title = '<h4>%s</h4>\n' % info['Course']
            body = '%s\n<table>\n%s</table>\n' % (title, body)
            url = 'mypurdue.purdue.edu'
            body += '\n\n\n<a href="http://%s">%s</a>\n' % (url, url)

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
            sendmail(sender, sender, subject, content)
            print '\n', 'email sent to %s' % receiver
        print '\n', json.dumps(info)


if __name__ == '__main__':
    main()
