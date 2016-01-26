import ssl
from hashlib import sha256

class ProofError(Exception):
    pass

def get_https_fingerprint(url):
    pem = ssl.get_server_certificate((url, 443), ca_certs=None)
    # not the correct way to get fingerprint
    return sha256(pem).hexdigest()

def construct_proof(url, fingerprint, nodeid):
    """The variable `nodeid` serves as a nonce and should perhaps be
    substituted for a random integer?

    The idea here is to calculate a unique hash that requires actually
    checking the server certificate. 
    """
    return sha256(fingerprint + url + nodeid).hexdigest()

def proof_of_check(url, nodeid):
    fingerprint = get_https_fingerprint(url)
    proof = construct_proof(url, fingerprint, nodeid)
    return fingerprint, proof

def verify_proof(url, fingerprint, nodeid, claimed_proof):
    if get_https_fingerprint(url) != fingerprint:
        return False
    elif construct_proof(url, fingerprint, nodeid) != claimed_proof:
        return False
    else:
        return True

