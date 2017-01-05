import os
import shutil
import tempfile
import unittest

from vrs.util.crypto import encrypt, decrypt
from vrs.util.crypto import genkeys, sign, verify
from vrs.util.crypto import SecretError, KeyGenError, InvalidKeyFile

class TestSecret(unittest.TestCase):
    def test_secret(self):
        x = encrypt("secret message", "password1234")        
        self.assertEqual(decrypt(x, "password1234"), "secret message")
        
    def test_large_secret(self):
        secret = os.urandom(10 * 1024 * 104)
        x = encrypt(secret, "password1234")
        self.assertEqual(decrypt(x, "password1234"), secret)

    def test_empty_secret(self):
        x = encrypt("", "password1234")
        self.assertEqual(decrypt(x, "password1234"), "")

    def test_corrupt_secret(self):
        x = encrypt("", "password1234")
        self.assertRaises(SecretError, decrypt, x + "!", "password1234")
        
    def test_corrupt_secret_password(self):
        x = encrypt("secret message", "password1234")
        self.assertRaises(SecretError, decrypt, x, "password4321")

        
class TestDigitalSignature(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.pubkeyfile = os.path.join(self.tempdir, "key.pub")
        self.privkeyfile = os.path.join(self.tempdir, "key.priv")
        genkeys(self.pubkeyfile, self.privkeyfile)
        
    def tearDown(self):
        shutil.rmtree(self.tempdir)
    
    def test_verify(self):
        message = "Test Message"
        blob = sign(self.privkeyfile, message)
        assert verify(self.pubkeyfile, message, blob)

    def test_corrupt(self):
        blob = sign(self.privkeyfile, "Test Message")
        assert not verify(self.pubkeyfile, "Corrupt Message", blob)

    def test_invalidkey(self):
        self.assertRaises(InvalidKeyFile, sign, "invalid.key", "Test Message")
        self.assertRaises(KeyGenError, genkeys, "", "")

if __name__ == '__main__':
   logging.getLogger().setLevel(logging.DEBUG)
   logging.getLogger().addHandler(logging.StreamHandler())
   unittest.TestLoader().loadTestsFromTestCase(TestSecret).debug()
   unittest.TestLoader().loadTestsFromTestCase(TestDigitalSignature).debug()
