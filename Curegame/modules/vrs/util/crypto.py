##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import os, sys
import base64
import cStringIO
import hmac

from hashlib import sha256
from M2Crypto import DSA, EVP

__all__ = ["genkeys", "sign", "verify", "encrypt", "decrypt"]

###########################################################################
# Protect data data using symmetric-key encryption.
###########################################################################

# M2Crypto wrapper for storing secrets (symmectric key using AES-256 bit in
# CBC-mode) using PBKDF2 key derivation algorithms. Uses sign-then-encrypt
# techinque as recommended in Practical Cryptography section 8.2.

class SecretError(Exception):
    """
    Base class for Secret errors.
    """


def filter_cipher(cipher, inf, outf):
    """
    Pipe (filter) data from StringIO objects ``inf`` to ``outf`` using
    ``cipher`` object. Returns data in ``outf`` as result.
    """
    while True:
        data = inf.read()
        if not data:
            break
        outf.write(cipher.update(data))
    outf.write(cipher.final())
    return outf.getvalue()


def cipher_encrypt(plaintext, key, iv, alg):
    """
    Run M2Crypto ``alg`` cipher on ``plaintext`` using ``key` and ``iv`` in
    encryption mode and return result as string.
    """
    assert len(key) == len(iv) == 32
    cipher = EVP.Cipher(alg=alg, key=key, iv=iv, op=1) # encrypt mode!
    pbuf = cStringIO.StringIO(plaintext)
    cbuf = cStringIO.StringIO()
    ciphertext = filter_cipher(cipher, pbuf, cbuf)
    pbuf.close()
    cbuf.close()
    assert ciphertext
    return ciphertext


def cipher_decrypt(ciphertext, key, iv, alg):
    """
    Run M2Crypto ``alg`` cipher on ``plaintext`` using ``key` and ``iv`` in
    decryption mode and return result as string.
    """
    assert len(key) == len(iv) == 32
    cipher = EVP.Cipher(alg=alg, key=key, iv=iv, op=0) # decrypt mode!
    pbuf = cStringIO.StringIO()
    cbuf = cStringIO.StringIO(ciphertext)
    plaintext = filter_cipher(cipher, cbuf, pbuf)
    pbuf.close()
    cbuf.close()
    return plaintext


def encrypt(cleartext, password):
    """
    Return encrypted version of ``cleartext`` using ``password``.
    """
    # Generate 256 bit random encryption salt.
    salt = os.urandom(32)

    # Derive 256 bit encryption key using the PBKDF2 standard.
    key = EVP.pbkdf2(password, salt, iter=1000, keylen=32)

    # Derive encryption key and HMAC key.
    hmac_key = sha256(key + 'M').digest()
    enc_key  = sha256(key + 'E').digest()

    # Generate 256 bit random initialization vector.
    iv = os.urandom(32)

    # Add HMAC to cleartext so that we can check during decrypt if we got the
    # right cleartext back. We are doing sign-then-encrypt, which let's us
    # encrypt empty cleartext (otherwise we'd need to pad with some string to
    # encrypt). Practical Cryptography by Schneier & Ferguson also recommends
    # doing it in this order in section 8.2.
    mac = hmac.new(hmac_key, iv + salt + cleartext, sha256).hexdigest()

    try:
        ciphertext = cipher_encrypt(mac + cleartext, enc_key, iv, "aes_256_cbc")
    except EVP.EVPError, e:
        raise SecretError(str(e))

    return iv + salt + ciphertext


def decrypt(ciphertext, password):
    """
    Return decrypted plaintext from ``cleartext`` using ``password``.
    """
    # Retrieve prepended (IV, SALT) components and isolate ciphertext.
    iv, salt, data = ciphertext[:32], ciphertext[32:64], ciphertext[64:]

    # derive 256 bit key using the PBKDF2 standard
    key = EVP.pbkdf2(password, salt, iter=1000, keylen=32)

    # Derive encryption key and HMAC key.
    hmac_key = sha256(key + 'M').digest()
    enc_key  = sha256(key + 'E').digest()

    try:
        data = cipher_decrypt(data, enc_key, iv, "aes_256_cbc")
    except EVP.EVPError, e:
        raise SecretError(str(e))

    # Retrieve prepended MAC component and isolate cleartext.
    mac, cleartext = data[:64], data[64:]

    # Verify integrity (MAC) of the decrypted plaintext data.
    if hmac.new(hmac_key, iv + salt + cleartext, sha256).hexdigest() != mac:
        raise SecretError('HMAC ciphertext mismatch')

    return cleartext


###########################################################################
# DigitalSignature.
###########################################################################

class KeyGenError(RuntimeError):
    """Error during DSA public/private key generation."""
    pass

class InvalidKeyFile(RuntimeError):
    """An invalid DSA public/privat key filepath was passed."""
    pass

class DigitalSignature():
    """
    Provide support for signing/verifying data integrity using 1024 bit DSA
    (SHA-1). The digital signature is encoded is stored in ASN1 format and is
    encoded to base64 to ease transporation and storage. The class can either
    be initialized for signing and/or verification depending on the DSA keys
    provided to the constructor.
    """

    def __init__(self, pubkeyfile=None, privkeyfile=None):
        """
        Initialize internal DSA cryptos with fully qualified paths to
        private/public key files. Passing a ``pubkeyfile`` will activate the
        verify() method while ``privkeyfile`` will activate the sign() method.
        """
        self.pub, self.priv = None, None
        if pubkeyfile:
            try:
                self.pub = DSA.load_pub_key(pubkeyfile)
            except IOError, e:
                raise InvalidKeyFile(pubkeyfile)
        if privkeyfile:
            try:
                self.priv = DSA.load_key(privkeyfile)
            except IOError, e:
                raise InvalidKeyFile(privkeyfile)

    def sha1(self, message):
        """Sign message using SHA-1."""
        md = EVP.MessageDigest('sha1')
        md.update(message)
        return md.final()

    def sign(self, message):
        """
        Generate digital signature for ``message`` using private DSA key in the
        form of a base64 encoded blob.
        """
        if not self.priv:
            raise RuntimeError("Missing private DSA key")
        asn1 = self.priv.sign_asn1(self.sha1(message))
        return base64.urlsafe_b64encode(asn1)

    def verify(self, message, blob):
        """
        Verify integrity of ``message`` using the digital signature ``blob``
        and the public DSA key ``pubkeyfile``.
        """
        if not self.pub:
            raise RuntimeError("Missing public DSA key")
        asn1 = base64.urlsafe_b64decode(blob)
        return self.pub.verify_asn1(self.sha1(message), asn1)

###########################################################################
# Utility methods.
###########################################################################

def genkeys(pubkeyfile, privkeyfile):
    """
    Generate a pair of public/private 1024 bit DSA keys and store them to the
    fully qualified paths ``pubkeyfile`` and ``privkeyfile``.
    """
    dsa = DSA.gen_params(1024, callback=lambda(p,n): None)
    dsa.gen_key()
    try:
        if not dsa.save_pub_key(pubkeyfile):
            raise IOError()
    except IOError, e:
        raise KeyGenError("Failed to save public DSA key: " + pubkeyfile)
    try:
        if not dsa.save_key(privkeyfile, None):
            raise IOError()
    except IOError, e:
        raise KeyGenError("Failed to save private DSA key: " + privkeyfile)

def sign(privkeyfile, message):
    """
    Generate digital signature for ``message`` using private DSA key
    ``privkeyfile`` in the form of a base64 encoded blob.
    """
    return DigitalSignature(privkeyfile=privkeyfile).sign(message)

def verify(pubkeyfile, message, blob):
    """
    Verify integrity of ``message`` using the digital signature ``blob`` and
    the public DSA key ``pubkeyfile``.
    """
    return DigitalSignature(pubkeyfile=pubkeyfile).verify(message, blob)


###########################################################################
# The End.
###########################################################################
