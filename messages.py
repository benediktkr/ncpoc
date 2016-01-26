import hmac
import json

import node

def create_hello(nodeid, version):
    msg = {'nodeid': nodeid,
           'versyion': version}
    sign = hmac.new(nodeid, json.dumps(msg))
    envelope = {'msg': msg,
                'sign': sign.hexdigest()}
    return json.dumps(envelope)

def validate_hello(envelope):
    envelope = json.loads(envelope)
    nodeid = str(envelope['msg']['nodeid'])
    signature = str(envelope['sign'])
    msg = json.dumps(envelope['msg'])
    verify_sign = hmac.new(nodeid, msg)
    return hmac.compare_digest(verify_sign.hexdigest(), signature)

    
    
