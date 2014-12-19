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


import urllib

from B2SProtocol.constants import CustomEnum
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from common.m17n import gettext as _

class ADDR_TYPE(CustomEnum):
    Shipping = 0
    Billing = 1

class FRT_ROUTE_ROLE(CustomEnum):
    HOMEPAGE = "HOMEPAGE"
    USER_AUTH = "USER_AUTH"
    USER_LOGOUT = "USER_LOGOUT"
    USER_INFO = "USER_INFO"
    MY_ACCOUNT = "MY_ACCOUNT"
    RESET_PWD_REQ = "RESET_PWD_REQ"
    RESET_PWD = "RESET_PWD"

    PRDT_LIST = "PRDT_LIST"
    PRDT_INFO = "PRDT_INFO"
    TYPE_LIST = "TYPE_LIST"
    BASKET = "BASKET"
    ORDER_LIST = "ORDER_LIST"
    ORDER_INFO = "ORDER_INFO"
    ORDER_AUTH = "ORDER_AUTH"
    ORDER_USER = "ORDER_USER"
    ORDER_ADDR = "ORDER_ADDR"
    ORDER_INVOICES = 'ORDER_INVOICES'
    PAYMENT = "PAYMENT"

class Redirection:
    def __init__(self, url, err):
        self.url = url
        self.err = err

    @property
    def redirect_to(self):
        redirect_to = self.url
        if self.err:
            redirect_to += "?%s" % urllib.urlencode({'err': self.err})
        return redirect_to


CURR_USER_BASKET_COOKIE_NAME = "CURR_%s" % USER_BASKET_COOKIE_NAME

# list user form labels to make them searchable for gettext
[
    _('Civility'),
    _('First name'),
    _('Last name'),
    _('Title'),
    _('Locale'),
    _('Gender'),
    _('Birthday'),
    _('Email'),
    _('Phone number'),
    _('Calling code'),
    _('Number'),
    _('Address'),
    _('Billing'),
    _('Shipping'),
    _('Both'),
    _('City'),
    _('Postal code'),
    _('Country'),
    _('Description'),
    _('Recipient'),
]

