#!/usr/bin/python2.7

import argparse
from datetime import datetime

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.error import CannotListenError
from twisted.internet.endpoints import connectProtocol

import network
from network import NCFactory, NCProtocol

def _print(*args):
    # double, make common module
    time = datetime.now().time().isoformat()[:8]
    print time,
    print "".join(map(str, args))


# Move this and network.BOOTSTRAP_NODES somewhere mode sensible
DEFAULT_PORT = 5005

parser = argparse.ArgumentParser(description="ncpoc")
parser.add_argument('--port', type=int, default=DEFAULT_PORT)
parser.add_argument('--listen', default="127.0.0.1")
parser.add_argument('--bootstrap', action="append", default=[])

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        endpoint = TCP4ServerEndpoint(reactor, args.port, interface=args.listen)
        _print(" [ ] LISTEN:", args.listen, ":", args.port)
        ncfactory = NCFactory()
        endpoint.listen(ncfactory)
    except CannotListenError:
        _print("[!] Address in use")
        raise SystemExit


    # connect to bootstrap addresses
    _print(" [ ] Trying to connect to bootstrap hosts:")
    for bootstrap in network.BOOTSTRAP_NODES + [a+":"+str(DEFAULT_PORT) for a in args.bootstrap]:

        _print("     [*] ", bootstrap)
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO", "SPEAKER"))
        d.addCallback(network.gotProtocol)
    reactor.run()
