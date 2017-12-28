# NameChain (Proof of Concept)

This is meant to be a proof-of-concept implementation of NameChain, a peer-to-peer verification of HTTP/SSL sites instead of the traditional CA system.

A blockchain may or may not be involved.

## Brief protocol explenation

The idea is based on both first-trust (like SSH) and the idea that a HTTPS/SSL server should be serving the same SSL certificates to any clients on the internet.

When a new HTTP/SSL site is "found", the certificate fingerprint is broadcast through the p2p network, along with a proof-of-check. Each participant in the p2p network will (with a random probability) then check the fingerprint and given proof-of-check. The probability that each given client will perform the check is determined by the number of participants in the network, to avoid hugging new sites to death. Or by having decidated "miners" and most clients wokring like an SPV client in Bitcion (i.e. are nodes in the network, but are not miners).

A new site can be found by anyone, not just it's owner. However, clients probably shouldn't automatically send out any new sites they encounter, as that would tell the whole network what this user is looking at. Either the miners have to crawl or something, or the data can be anonamized somehow. Maybe using Tor to send the data to the miner is plausible, since the delay from finding a new site to having it verified by the network could tolerate delay in seconds. At least its good enough to try.

Sites could be manually entered into the system, but that seems tedious.

Depending on the scale, nodes in the p2p network might not be able to hold the full chain

## Blockchains

Everyone wants **a blockchain** these days. A bitcoin-like blockchain probably wont be of much use here, as we went to look up urls's and not transaction id's.

The word "minig" doesn't really work as an analogy. It's not mining, it's verifying. But "verifier" isn't much of an analogy.

## proof-of-check

Let's try

```
proof-of-check = HMAC(key=node_id, url || ssl_fingerprint)
```


But anybody can create that hash, if they know the `node_id` and the url. s
