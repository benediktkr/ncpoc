
import sys
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
    print " ".join(map(str, args))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 5005
    try:
        endpoint = TCP4ServerEndpoint(reactor, port, interface="151.217.219.153")
        _print(" [ ] LISTEN:", port)
        ncfactory = NCFactory()
        endpoint.listen(ncfactory)
    except CannotListenError:
        _print("[!] Address in use")
        sys.exit(1)


    # connect to bootstrap addresses
    _print(" [ ] Trying to connect to bootstrap hosts:")
    for bootstrap in network.BOOTSTRAP_NODES:
        _print("     [*]", bootstrap)
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO", "SPEAKER"))
        d.addCallback(network.gotProtocol)
    reactor.run()
