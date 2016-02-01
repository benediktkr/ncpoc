import sys
sys.path.append("..")
import unittest

import proof
import cryptotools

class TestProof(unittest.TestCase):
    def setUp(self):
        self.nodeid = cryptotools.generate_nodeid()

    def tearDown(self):
        pass

    def test_proof(self):
        for url in ["sudo.is", "lokun.is", "microsoft.com"]:
            pocheck = proof.proof_of_check(url, self.nodeid)
            ver = proof.verify_proof(url, pocheck[0], self.nodeid, pocheck[1])
            self.assertTrue(ver)


if __name__ == "__main__":
    unittest.main()            
