import sys
sys.path.append("..")
import unittest

import proof
import messages
import node

class TestMessages(unittest.TestCase):
    def setUp(self):
        self.nodeid = node.generate_nodeid()

    def tearDown(self):
        pass

    def test_hello(self):
        hello = messages.create_hello(self.nodeid, 0)
        # check that InvalidSignatureError is not raised
        return messages.read_message(hello)

    def test_ackhello(self):
        ackhello = messages.create_ackhello(self.nodeid)
        return messages.read_message(ackhello)

class TestProof(unittest.TestCase):
    def setUp(self):
        self.nodeid = node.generate_nodeid()

    def tearDown(self):
        pass

    def test_proof(self):
        for url in ["sudo.is", "lokun.is", "microsoft.com"]:
            pocheck = proof.proof_of_check(url, self.nodeid)
            ver = proof.verify_proof(url, pocheck[0], self.nodeid, pocheck[1])
            self.assertTrue(ver)


if __name__ == "__main__":
    unittest.main()            
