# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


# users.backtoshops.com settings
from settings_base import *

SELLER_EMAIL = 'business@infinite-code.com'

### Paybox
PAYBOX_REQUEST_URL = 'https://preprod-tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi'
PAYBOX_DIRECT_REQUEST_URL = 'https://preprod-ppps.paybox.com/PPPS.php'

# no-3D
PAYBOX_SITE = '1999888'
PAYBOX_RANG = '32'
PAYBOX_IDENTIFIANT = '1686319'
PAYBOX_CLE = '1999888I'

#3D
# PAYBOX_SITE = '1999888'
# PAYBOX_RANG = '43'
# PAYBOX_IDENTIFIANT = '107975626'

#
# PAYBOX_SITE = '7830331'
# PAYBOX_RANG = '16'
# PAYBOX_IDENTIFIANT = '537370176'

PAYBOX_HMAC_KEY = '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF'
# PAYBOX_HMAC_KEY = '11E83FB4C0D2DA9458A7B67463B7A478771CDA3403DBBAB3A871018F78A0DC7DE2939966F4EB1894C550AF236A1A40CFF888E21A1BA5BE60A073F913E226AD2A'


### Stripe
STRIPE_PUBLISH_API_KEY = 'pk_test_MmEgOJaC6wytcwAqoX8IFxnF'
STRIPE_SECRET_API_KEY = 'sk_test_uS50BVM0fmdsxxJyDcWqeyAB'
