# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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

