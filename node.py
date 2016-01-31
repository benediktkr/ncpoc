import os
import hashlib

bootstrap_list = ["localhost:5005",
                  "localhost:5006",
                  "localhost:5007",
                  "localhost:5008"]

def generate_nodeid():
    return hashlib.sha256(os.urandom(256/8)).hexdigest()
