import os
import hashlib

bootstrap_list = ["localhost:5005"]

def generate_nodeid():
    return hashlib.sha256(os.urandom(256/8)).hexdigest()
