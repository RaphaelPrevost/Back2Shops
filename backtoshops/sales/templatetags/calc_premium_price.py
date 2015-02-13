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


import logging
from django import template

register = template.Library()

@register.simple_tag
def calc_premium_price(premium_type, premium_amount, price):
    if premium_amount is None:
        return price
    try:
        premium_amount = float(premium_amount)
        price = float(price)
        if premium_type == "percentage":
            tmp = price + (price * (premium_amount / 100))
            return round(tmp * 100 + ((tmp * 1000 % 10 > 4) and 1 or 0)) / 100
        else:
            return price + premium_amount;
    except Exception, e:
        logging.warn('Error happened when calculating premium price, '
                     'premium_type: %s, premium_amount: %s, price: %s, '
                     'error: %s', premium_type, premium_amount, price, e)
    return None
