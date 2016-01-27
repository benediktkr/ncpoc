import hmac
import json

class InvalidSignatureError(Exception):
    pass

def make_envelope(msg):
    nodeid = msg['nodeid']
    sign = hmac.new(nodeid, json.dumps(msg))
    envelope = {'msg': msg,
                'sign': sign.hexdigest()}
    return json.dumps(envelope)


# ------

def create_ackhello(nodeid):
    msg = {'name': 'ackhello',
           'nodeid': nodeid}
    return make_envelope(msg)

def create_hello(nodeid, version):
    msg = {'nodeid': nodeid,
           'version': version,
           'name': 'hello'}
    return make_envelope(msg)

# -------

def read_message(envelope):
    envelope = json.loads(envelope)
    nodeid = str(envelope['msg']['nodeid'])
    signature = str(envelope['sign'])
    msg = json.dumps(envelope['msg'])
    verify_sign = hmac.new(nodeid, msg)
    if hmac.compare_digest(verify_sign.hexdigest(), signature):
        return envelope
    else:
        raise InvalidSignatureError


    
    
