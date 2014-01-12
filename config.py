import json

from util import set_timezone, log


conf = {}

def load_conf(filename):
    __conf__ = None
    with open(filename) as f:
        r = f.read()
        __conf__ = json.loads(r)

    if __conf__ == None:
        raise Exception('load configuration %s failed' % filename)

    for key, val in __conf__.items():
        _c = val
        if type(_c) == dict:
            if key not in conf:
                conf[key] = type(_c)()
            c = conf[key]
            for subkey in _c:
                c[subkey] = _c[subkey]
        else:
            conf[key] = val

    set_timezone(conf['sys']['timezone'])

def load_default_conf():
    if check_test_mode():
        load_conf('local.conf')
    else:
        load_conf('prod.conf')

def check_test_mode():
    try:
        with open('TEST') as f:
            pass
        log('TEST MODE')
        conf['test-mode'] = True
        return conf['test-mode']
    except:
        pass
    return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        load_conf(sys.argv[1])
        log(conf)
