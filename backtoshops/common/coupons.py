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


import settings
import logging
import ujson
import urllib
import xmltodict

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from common.actors.coupon import ActorCoupons
from common.error import UsersServerError


def post_coupon(id_brand, id_bo_user, **kwargs):
    try:
        data = {
            'action': 'create',
            'id_issuer': id_brand,
            'author': id_bo_user,
        }
        data.update(kwargs)
        rst = get_from_remote(settings.COUPON_CREATE_URL,
                        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                        settings.PRIVATE_KEY_PATH,
                        data=urllib.urlencode(data),
                        headers={'Content-Type': 'x-www-form-urlencoded'})

        coupons_data = xmltodict.parse(rst)
        return coupons_data['coupons']['coupon']['@id']

    except Exception, e:
        logging.error("Failed to create coupon %s" % data,
                      exc_info=True)


def create_item_specific_coupon(id_brand, id_bo_user, id_sale, discount_ratio,
                                valid_from, valid_to):
    kwargs = {
        'reward_type': 'COUPON_DISCOUNT',
        'discount_applies_to': 'VALUE_MATCHING',
        'discount': discount_ratio,
        'require': ujson.dumps({
            "invoice_match":{"sale": [id_sale]}
        }),
    }
    if valid_from:
        kwargs['creation_time'] = str(valid_from)
    if valid_to:
        kwargs['expiration_time'] = str(valid_to)

    return post_coupon(id_brand, id_bo_user, **kwargs)


def delete_coupon(id_brand, id_bo_user, id_coupon):
    kwargs = {
        'action': 'delete',
        'id_coupon': id_coupon,
    }
    return post_coupon(id_brand, id_bo_user, **kwargs)


def get_coupons(id_brand, id_shop=None, id_sale=None,
                product_brand=None, promotion_group=None):
    query = [('id_brand', id_brand)]
    if id_shop:
        if not isinstance(id_shop, list):
            id_shop = [id_shop]
        for _id in id_shop:
            query.append(('id_shop', _id))
    if id_sale:
        query.append(('id_item', id_sale))
    if product_brand:
        query.append(('item_brand', product_brand))
    if promotion_group:
        query.append(('promotion_group', promotion_group))

    try:
        url = "{}?{}".format(settings.COUPON_LIST_URL, urllib.urlencode(query))
        rst = get_from_remote(url,
                        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                        settings.PRIVATE_KEY_PATH,
                        headers={'Content-Type': 'x-www-form-urlencoded'})

        coupons_data = xmltodict.parse(rst)
        return ActorCoupons(coupons_data)

    except Exception, e:
        logging.error("Failed to get coupon %s" % query,
                      exc_info=True)

def get_item_specific_discount_coupon(id_brand, id_sale):
    coupons_actor = get_coupons(id_brand, id_sale=id_sale)
    for coupon in coupons_actor.coupons:
        if coupon.type != 'COUPON_DISCOUNT':
            continue
        if coupon.reward.rebate.type != 'VALUE_MATCHING':
            continue
        return coupon

    return None
