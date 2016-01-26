# NameChain (Proof of Concept)

This is meant to be a proof-of-concept implementation of NameChain, a peer-to-peer verification of HTTP/SSL sites instead of the traditional CA system.

A blockchain may or may not be involved.

## Brief protocol explenation

I feel that it is pointless to list out the flaws of the CA system. This is not the place to do that, this is merely an exploration of an alternative idea.

The idea is based on both first-trust (like SSH) and the idea that a HTTPS/SSL server should be serving the same SSL certificates to any clients on the internet.

When a new HTTP/SSL site is "found" (mined?), the certificate fingerprint is broadcast through the p2p network, along with a proof-of-check. Each participant in the p2p network will (with a random probability) then check the fingerprint and given proof-of-check. The probability that each given client will perform the check is determined by the number of participants in the network, to avoid hugging new sites to death.

A new site can be found by anyone, not just it's owner. However, clients probably shouldn't automatically send out any new sites they encounter, as that would tell the whole network what this user is looking at.

Sites could be manually entered into the system, but that seems tedious. Consider this an open practical question.

Depending on the scale, nodes in the p2p network might not be able to hold the full NameChain. 

## proof-of-check

Based on the concept of proof-of-work in Bitcoin.

```
proof-of-check = HMAC(key=node_id, url || ssl_fingerprint)
```

Proves that a node opened an SSL connection to a server at `url` and read the fingerprint. To verify, a node will connect to `url` and read the fingerprint byt itself, then calculate the HMAC to verify that it saw the same certificate that the node given by `nodeid` did. 
