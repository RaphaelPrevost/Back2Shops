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


from B2SProtocol.constants import CustomEnum

class FIELD_TYPE(CustomEnum):
    TEXT = "text"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FIELDSET = "fieldset"
    AJAX = "ajax"

class GENDER(CustomEnum):
    Male = "M"
    Female = "F"
    Other = "O"

class ADDR_TYPE(CustomEnum):
    Shipping = 0
    Billing = 1
    Both = 2

class HASH_ALGORITHM(CustomEnum):
    WHIRLPOOL = 1
    SHA256 = 2


class RETURN_STATUS(CustomEnum):
    RETURN_ELIGIBLE = 1
    RETURN_REJECTED = 2 #1 << 1
    RETURN_RECEIVED = 4 #1 << 2
    RETURN_EXAMINED = 8 #1 << 3
    RETURN_ACCEPTED = 16 #1 << 4
    RETURN_REJECTED = 32 #1 << 5
    RETURN_PROPOSAL = 64 #1 << 6
    RETURN_REFUNDED = 128 #1 << 7
    RETURN_REJECTED_FRAUD = 256 #1 << 8
    RETURN_REJECTED_INVAL = 512 #1 << 9
    RETURN_PROPOSAL_ACCEPT = 1024 #1 << 10
    RETURN_PROPOSAL_REJECT = 2048 #1 << 11

class TICKET_PRIORITY(CustomEnum):
    IMPORTANT = 1
    MAJOR = 2
    NORMAL = 3
    MINOR = 4
    TRIVIAL = 5

class TICKET_FEEDBACK(CustomEnum):
    USEFUL = 1
    USELESS = 2

HASH_ALGORITHM_NAME = {
    HASH_ALGORITHM.WHIRLPOOL: "whirlpool",
    HASH_ALGORITHM.SHA256: "sha256",
}

PAYPAL_VERIFIED = 'VERIFIED'
PAYPAL_INVALID = 'INVALID'

RESET_PASSWORD_REDIS_KEY = 'RESET_PWD:%s'


class COUPON_CONDITION_IDTYPE(CustomEnum):
    SALE = 1
    SHOP = 2
    BRAND = 3 # product brand
    GROUP = 4 # promotion group

class COUPON_CONDITION_OPERATION(CustomEnum):
    NONE = 1
    SUM_ITEMS = 2
    SUM_PRICE = 3
    MATCH_ALL = 4

class COUPON_CONDITION_COMPARISON(CustomEnum):
    LT = 1
    LTE = 2
    EQ = 3
    GT = 4
    GTE = 5

class COUPON_REWARD_TYPE(CustomEnum):
    COUPON_CURRENCY = 1
    COUPON_DISCOUNT = 2
    COUPON_GIVEAWAY = 3

class COUPON_DISCOUNT_APPLIES(CustomEnum):
    VALUE_CHEAPEST = 1
    VALUE_MATCHING = 2
    VALUE_INVOICED = 3
    VALUE_SHIPPING = 4

class ORDER_STATUS_FOR_COUPON(CustomEnum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3

