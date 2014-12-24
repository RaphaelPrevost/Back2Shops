# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import logging
import ujson
import urllib2
import os

import M2Crypto
from base64 import b64encode, b64decode
from M2Crypto import RSA, BIO, EVP

ENC = 1
DEC = 0
BLOCK_SIZE = 16


def _pad(text):
    BS = BLOCK_SIZE
    return text + (BS - len(text) % BS) * chr(BS - len(text) % BS)

def _unpad(text):
    return text[0:-ord(text[-1])]


class CustomCipher(object):
    def __init__(self, key):
        pass


class CBCCipher(CustomCipher):
    def __init__(self, key):
        super(CBCCipher, self).__init__(key)
        self.key = b64encode(key)
        self.mode = 'aes_256_cbc'

    def encrypt(self, data):
        data = b64encode(data)
        iv = os.urandom(BLOCK_SIZE)

        cipher = self.get_cipher(iv, ENC)
        v = cipher.update(iv + data)
        v = v + cipher.final()
        del cipher
        v = b64encode(v)
        return v

    def decrypt(self, data):
        data = b64decode(data)
        iv = data[:BLOCK_SIZE]
        cipher = self.get_cipher(iv, DEC)
        v = cipher.update(data[BLOCK_SIZE:])
        v = v + cipher.final()
        del cipher
        return b64decode(v)

    def get_cipher(self, iv, op=ENC):
        key = b64decode(self.key)
        return EVP.Cipher(alg=self.mode,
                                   key=key,
                                   iv=iv,
                                   op=op)


class PaddingCipher(CustomCipher):
    def __init__(self, key):
        super(PaddingCipher, self).__init__(key)
        self.key = key
        self.max_block_size = 256

    def pri_encrypt(self, data):
        data = b64encode(data)
        rsa = self._pri_rsa()

        result = ''
        index = 0
        block_size = self.max_block_size / 2
        while data[index:]:
            data_block = data[index:index + block_size]
            en_block = rsa.private_encrypt(data_block, RSA.pkcs1_padding)
            result += en_block
            index += block_size

        return b64encode(result)

    def pub_decrypt(self, data):
        data = b64decode(data)
        rsa = self._pub_rsa()

        result = ''
        index = 0
        while data[index:]:
            data_block = data[index:index + self.max_block_size]
            de_data = rsa.public_decrypt(data_block, RSA.pkcs1_padding)
            result += de_data
            index += self.max_block_size

        return b64decode(result)

    def pub_encrypt(self, data):
        data = b64encode(data)
        rsa = self._pub_rsa()
        result = ''
        index = 0
        block_size = self.max_block_size / 2
        while data[index:]:
            data_block = data[index:index + block_size]
            en_block = rsa.public_encrypt(data_block, RSA.pkcs1_oaep_padding)
            result += en_block
            index += block_size

        return b64encode(result)

    def pri_decrypt(self, data):
        data = b64decode(data)
        rsa = self._pri_rsa()
        result = ''
        index = 0
        while data[index:]:
            data_block = data[index:index + self.max_block_size]
            de_data = rsa.private_decrypt(data_block, RSA.pkcs1_oaep_padding)
            result += de_data
            index += self.max_block_size

        return b64decode(result)

    def _pri_rsa(self):
        rsa = RSA.load_key_string(self.key)
        return rsa

    def _pub_rsa(self):
        bio = BIO.MemoryBuffer(self.key)
        rsa = RSA.load_pub_key_bio(bio)
        return rsa


def aes_encrypt_content(content, random_key, pub_key, pri_key):
    # use random_key to encrypt content
    content = CBCCipher(random_key).encrypt(content)

    # use remote public key to encrypt the random key.
    random_key1 = PaddingCipher(pub_key).pub_encrypt(random_key)

    # use own private key to do second time encrypt for the random key.
    random_key2 = PaddingCipher(pri_key).pri_encrypt(random_key1)

    return content, random_key2

def aes_decrypt_content(en_content, en_random_key, pub_key, pri_key):
    # use remote public key to decrypt en_random_key
    pub_random_key = PaddingCipher(pub_key).pub_decrypt(en_random_key)

    # use own private key to decrypt decrypted en_random_key
    random_key = PaddingCipher(pri_key).pri_decrypt(pub_random_key)

    # use random_key to decrypt en_content
    content = CBCCipher(random_key).decrypt(en_content)

    return content

RANDOM_KEY_SIZE = 32 # (*AES-256*)
def gen_encrypt_json_context(context, api_key_uri, api_key_path):
    if isinstance(context, unicode):
        context = unicode.encode(context, 'utf8')
    random_key = os.urandom(RANDOM_KEY_SIZE)
    pub_key = get_key_from_remote(api_key_uri)
    pri_key = get_key_from_local(api_key_path)
    en_body, en_key = aes_encrypt_content(context, random_key,
                                          pub_key, pri_key)
    resp_body = {'content': en_body,
                 'key': en_key}

    return ujson.dumps(resp_body)

def decrypt_json_resp(resp, api_key_uri, api_key_path):
    body = resp.read()
    body = ujson.loads(body)
    en_content = body['content']
    en_key = body['key']

    pub_key = get_key_from_remote(api_key_uri)
    pri_key = get_key_from_local(api_key_path)

    body = aes_decrypt_content(en_content, en_key, pub_key, pri_key)
    return body

def get_key_from_local(path):
    with open(path) as f:
        key = f.read()
        f.close()
        return key

def get_key_from_remote(uri):
    try:
        resp = urllib2.urlopen(uri)
        return resp.read()
    except urllib2.HTTPError, e:
        logging.error('Failed to get public key form %s with error %s',
                      uri, str(e))
        raise

def get_from_remote(uri, api_key_uri, api_key_path, data=None, headers={}):
    req = urllib2.Request(uri, data=data, headers=headers)
    try:
        resp = urllib2.urlopen(req)
        return decrypt_json_resp(resp, api_key_uri, api_key_path)
    except urllib2.HTTPError, e:
        logging.error('get_from_remote HTTPError: '
                      'error: %s, '
                      'with uri: %s, data :%s, headers: %s'
                      % (e, uri, data, headers), exc_info=True)
        raise
