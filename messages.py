import hmac
import json
import cryptotools

nonce = lambda: cryptotools.generate_random(64)
incr_nonce = lambda env: format(int(env["data"]["nonce"], 16) + 1, 'x')

class InvalidSignatureError(Exception):
    pass

def make_envelope(msgtype, msg, nodeid, thisnonce=None):
    msg['nodeid'] = nodeid
    msg['nonce'] = thisnonce or nonce()
    sign = hmac.new(nodeid, json.dumps(msg))
    envelope = {'data': msg,
                'sign': sign.hexdigest(),
                'msgtype': msgtype}
    return json.dumps(envelope)

# ------

def create_ackhello(nodeid):
    msg = {}
    return make_envelope("ackhello", msg, nodeid)

def create_hello(nodeid, version):
    msg = {'version': version}
    return make_envelope("hello", msg, nodeid)

def create_ping(nodeid):
    msg = {}
    return make_envelope("ping", msg, nodeid)

def create_pong(nodeid, pingmsg):
    nonce = incr_nonce(pingmsg)
    msg = {}
    return make_envelope("pong", msg, nodeid, nonce)

# -------

def read_message(envelope):
    # Nonce should be validated one level above this
    envelope = json.loads(envelope)
    nodeid = str(envelope['data']['nodeid'])
    signature = str(envelope['sign'])
    msg = json.dumps(envelope['data'])
    verify_sign = hmac.new(nodeid, msg)
    if hmac.compare_digest(verify_sign.hexdigest(), signature):
        return envelope
    else:
        raise InvalidSignatureError


    
    
