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


import types
from decimal import Decimal

from common import carriers
from shippings.models import Carrier, Service

def _api_fee(carr_cls, data):
    handling_fee = Decimal(data.get('handling_fee') or 0)
    addr_orig = data.get('addr_orig')
    addr_dest = data.get('addr_dest')
    service = data.get('service')
    weight = float(data.get('weight') or 0)

    rate = carr_cls.getRate(addr_orig, addr_dest, service, weight)
    return Decimal(rate) + handling_fee

def _no_api_fee(data):
    return Decimal(data.get('ship_and_handling_fee') or 0)

def compute_fee(data):
    carrer_id = data.get('carrier')
    carr = Carrier.objects.get(pk=carrer_id)
    carr_flag = carr and carr.flag
    cls_name = carr_flag.upper() + carriers.CARRIER_CLS_SURFFIX
    cls = getattr(carriers, cls_name, None)
    if cls and type(cls) is types.ClassType:
        total_fee = _api_fee(cls, data)
    else:
        total_fee = _no_api_fee(data)
    return total_fee
