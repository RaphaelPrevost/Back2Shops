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
def calc_discount_price(discount_type, discount, base_price, rounding=True):
    try:
        discount = float(discount)
        base_price = float(base_price)
        if discount_type == "percentage":
            tmp = base_price - (base_price * (discount / 100))
        else:
            tmp = base_price - discount

        if not rounding:
            return tmp
        return round(int(tmp * 100) + (int(tmp * 1000 % 10) > 4 and 1 or 0)) / 100
    except Exception, e:
        logging.warn('Error happened when calculating discount price, '
                     'discount_type: %s, discount: %s, base_price: %s, '
                     'error: %s', discount_type, discount, base_price, e)
    return None

@register.simple_tag
def calc_price_with_tax(price, tax_rate, input_after_tax_price=False):
    if input_after_tax_price:
        tmp = price / float(1 + tax_rate / 100.0)
    else:
        tmp = price * float(1 + tax_rate / 100.0)
    return round(int(tmp * 100) + (int(tmp * 1000 % 10) > 4 and 1 or 0)) / 100

@register.simple_tag
def calc_discount_price_with_tax(discount_type, discount, base_price, tax_rate,
                                 input_after_tax_price=False):
    price = calc_discount_price(discount_type, discount, base_price, rounding=False)
    return calc_price_with_tax(price, tax_rate, input_after_tax_price)

