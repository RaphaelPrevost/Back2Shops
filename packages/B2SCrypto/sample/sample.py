import os

from B2SCrypto.utils import CBCCipher
from B2SCrypto.utils import PaddingCipher
from B2SCrypto.utils import get_key_from_local


def cbccipher_sample():
    key = os.urandom(32)
    text = 't'
    en = CBCCipher(key).encrypt(text)
    de = CBCCipher(key).decrypt(en)
    assert de == text
    print 'aes encrypt/decrypt success'

def paddingcipher_sample():
    usr_pub = get_key_from_local('sample_keys/usr_pub.key')
    usr_pri = get_key_from_local('sample_keys/usr_pri.key')

    data = 'text'
    text = data * 1000
    en = PaddingCipher(usr_pub).pub_encrypt(text)
    de = PaddingCipher(usr_pri).pri_decrypt(en)

    assert text == de
    print 'public encrypt private decrypt success'

    en = PaddingCipher(usr_pri).pri_encrypt(text)
    de = PaddingCipher(usr_pub).pub_decrypt(en)

    assert text == de
    print 'private encrypt, public decrypt success'

cbccipher_sample()
paddingcipher_sample()

