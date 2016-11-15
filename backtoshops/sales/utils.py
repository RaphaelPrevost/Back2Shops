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


from attributes.models import BrandAttribute
from sales.models import ExternalRef
from sales.models import TypeAttributePrice

def get_sale_orig_price(sale, type_attribute_id):
    if not type_attribute_id or int(type_attribute_id) == 0:
        return sale.product.normal_price
    else:
        attr_price = TypeAttributePrice.objects.get(
            sale=sale,
            type_attribute_id=type_attribute_id)
        return attr_price.type_attribute_price

def get_sale_discounted_price(sale,
                            type_attribute_price=None,
                            orig_price=None):
    if orig_price is None:
        orig_price = get_sale_orig_price(sale, type_attribute_price)
    if sale.product.discount:
        if sale.product.discount_type == 'percentage':
            return orig_price * (1 - sale.product.discount / 100.0)
        else:
            return orig_price - sale.product.discount
    else:
        return orig_price

def get_sale_premium(price, id_variant):
    premium = 0
    if id_variant:
        variant = BrandAttribute.objects.get(pk=id_variant)
        if variant.premium_type and variant.premium_amount:
            if variant.premium_type == 'fixed':
                premium = variant.premium_amount
            elif variant.premium_type == 'percentage':
                premium = price * variant.premium_amount/100
    return premium

def get_sale_external_id(id_sale, id_variant, id_type):
    try:
        obj = ExternalRef.objects.get(sale_id=id_sale,
                               common_attribute_id=(id_type or None),
                               brand_attribute_id=(id_variant or None))
        return obj.external_id or ''
    except ExternalRef.DoesNotExist:
        return ''

