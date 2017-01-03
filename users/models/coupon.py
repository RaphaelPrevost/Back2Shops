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

from datetime import datetime
import logging
import ujson

from B2SProtocol.constants import SALE
from B2SProtocol.constants import SHOP
from B2SUtils import db_utils
from B2SUtils.base_actor import as_list
from B2SUtils.common import to_round
from B2SUtils.errors import ValidationError
from common.cache import group_cache_proxy
from common.cache import tax_cache_proxy
from common.constants import ADDR_TYPE
from common.constants import COUPON_CONDITION_IDTYPE
from common.constants import COUPON_CONDITION_OPERATION
from common.constants import COUPON_CONDITION_COMPARISON
from common.constants import COUPON_DISCOUNT_APPLIES
from common.constants import COUPON_REWARD_TYPE
from common.constants import ORDER_STATUS_FOR_COUPON
from common.redis_utils import get_redis_cli
from models.actors.sale import CachedSale
from models.order import get_order_items
from models.order import _create_order_details
from models.order import _create_order_item
from models.shipments import get_shipments_by_order
from models.shipments import get_shipping_list
from models.shipments import get_shipping_fee
from models.shipments import update_shipping_fee
from models.user import get_user_address


COUPON_FIELDS_COLUMNS = [
    ('id', 'coupons.id'),
    ('id_brand', 'id_brand'),
    ('id_bo_user', 'id_bo_user'),
    ('coupon_type', 'coupon_type'),
    ('creation_time', 'creation_time'),
    ('expiration_time', 'expiration_time'),
    ('stackable', 'stackable'),
    ('redeemable_always', 'redeemable_always'),
    ('max_redeemable', 'max_redeemable'),
    ('first_order_only', 'first_order_only'),
    ('password', 'password'),
    ('description', 'description'),
    ('manufacturer', 'manufacturer'),
]

def get_coupon_user_data(conn, id_coupon):
    id_users = db_utils.select(
        conn, 'coupon_given_to',
        columns=('id_user',),
        where={'id_coupon': id_coupon})
    if id_users:
        id_users = [v[0] for v in id_users]
    return id_users

def get_coupon_shop_data(conn, id_coupon):
    id_shops = db_utils.select(
        conn, 'coupon_accepted_at',
        columns=('id_shop',),
        where={'id_coupon': id_coupon})
    if id_shops:
        id_shops = [id_shop[0] for id_shop in id_shops]
    return id_shops

def get_coupon_condition_data(conn, id_coupon):
    match = []
    operation = None
    threshold = None
    cond_values = db_utils.select_dict(
        conn, 'coupon_condition', 'id',
        where={'id_coupon': id_coupon})
    if cond_values:
        for cond_value in cond_values.itervalues():
            operation = cond_value['operation']
            if cond_value['id_value'] and cond_value['id_type']:
                match.append({
                    'id': cond_value['id_value'],
                    'id_type': cond_value['id_type'],
                    'type_name': COUPON_CONDITION_IDTYPE.toReverseDict()[
                        cond_value['id_type']].lower(),
                })
            if cond_value['operation'] in (
                        COUPON_CONDITION_OPERATION.SUM_ITEMS,
                        COUPON_CONDITION_OPERATION.SUM_PRICE,
                    ):
                _threshold = {
                    'operation_name': 'items' if cond_value['operation'] ==
                        COUPON_CONDITION_OPERATION.SUM_ITEMS else 'price',
                    'comparison_name':
                        COUPON_CONDITION_COMPARISON.toReverseDict()[
                        cond_value['comparison']],
                    'comparison': cond_value['comparison'],
                    'threshold': cond_value['threshold'],
                }
                if threshold:
                    assert threshold == _threshold
                else:
                    threshold = _threshold
    return match, operation, threshold

def match_comparison(comparison, threshold, value):
    if comparison == COUPON_CONDITION_COMPARISON.LT:
        return value < threshold
    elif comparison == COUPON_CONDITION_COMPARISON.LTE:
        return value <= threshold
    elif comparison == COUPON_CONDITION_COMPARISON.EQ:
        return value == threshold
    elif comparison == COUPON_CONDITION_COMPARISON.GT:
        return value > threshold
    elif comparison == COUPON_CONDITION_COMPARISON.GTE:
        return value >= threshold

def order_item_match_cond(order_item, conds, id_brand, id_shops):
    if order_item['brand_id'] != id_brand:
        return False
    if id_shops and order_item['shop_id'] not in id_shops:
        return False

    sale_conds = [m['id'] for m in conds
                  if m['id_type'] == COUPON_CONDITION_IDTYPE.SALE]
    shop_conds = [m['id'] for m in conds
                  if m['id_type'] == COUPON_CONDITION_IDTYPE.SHOP]
    brand_conds = [m['id'] for m in conds
                  if m['id_type'] == COUPON_CONDITION_IDTYPE.BRAND]

    result_conds = []
    if sale_conds:
        result_conds.append(any([
            id_ == order_item['sale_id'] for id_ in sale_conds]))
    if shop_conds:
        result_conds.append(any([
            id_ == order_item['shop_id'] for id_ in shop_conds]))
    if brand_conds:
        item_detail = ujson.loads(order_item['item_detail'])
        result_conds.append(any([
            str(id_) == item_detail.get('product_brand', {}).get('id')
            for id_ in brand_conds]))
    return all(result_conds)

def order_items_match_group(order_items, groups, conds, operation):
    group_conds = [m['id'] for m in conds
                   if m['id_type'] == COUPON_CONDITION_IDTYPE.GROUP]
    for id_group in group_conds:
        group = groups.get(str(id_group))
        if not group:
            continue

        group_sales = [int(s['@id']) for s in as_list(group['sales']['sale'])]
        matched_items = [o['sale_id'] for o in order_items
                         if o['brand_id'] == int(group['brand']['@id'])
                            and o['shop_id'] == int(group['shop']['@id'])
                            and o['sale_id'] in group_sales]
        if operation == COUPON_CONDITION_OPERATION.MATCH_ALL:
            if len(set(matched_items)) == len(group_sales):
                return True
        else:
            if len(matched_items) > 0:
                return True
    return False


def check_coupon_with_password(conn, password, users_id, id_order, user_info):
    coupons = db_utils.select_dict(
        conn, 'coupons', 'id',
        where={'password': password, 'valid': True}).values()
    if len(coupons) == 0:
        raise ValidationError('COUPON_ERR_INVALID_PASSWORD')
    coupon = coupons[0]

    id_users = get_coupon_user_data(conn, coupon['id'])
    if id_users and int(users_id) not in id_users:
        raise ValidationError('COUPON_ERR_INVALID_COUPON')

    if coupon['expiration_time'] and \
            coupon['expiration_time'] < datetime.now():
        raise ValidationError('COUPON_ERR_INVALID_COUPON')

    results = db_utils.query(conn,
        "select id from coupon_redeemed "
        "where id_order=%s and id_coupon=%s and order_status in (%s,%s) "
        "union "
        "select id from store_credit_redeemed "
        "where id_order=%s and id_coupon=%s and order_status in (%s,%s) ",
        [id_order, coupon['id'],
         ORDER_STATUS_FOR_COUPON.PENDING,
         ORDER_STATUS_FOR_COUPON.PAID] * 2)
    if len(results) > 0:
        raise ValidationError('COUPON_ERR_APPLIED_COUPON')

    if not coupon['stackable']:
        results = db_utils.query(conn,
            "select id from coupon_redeemed "
            "where id_order=%s and order_status in (%s, %s) "
            "union "
            "select id from store_credit_redeemed "
            "where id_order=%s and order_status in (%s, %s) ",
            [id_order,
             ORDER_STATUS_FOR_COUPON.PENDING,
             ORDER_STATUS_FOR_COUPON.PAID] * 2)
        if len(results) > 0:
            raise ValidationError('COUPON_ERR_NOT_STACKABLE_COUPON')

    if coupon['max_redeemable']:
        if _get_redeemed_times(conn, coupon['id']) >= coupon['max_redeemable']:
            raise ValidationError('COUPON_ERR_USED_COUPON')

    if not coupon['redeemable_always']:
        if _once_coupon_limited(conn, id_coupon, users_id,
            user_info['fo_user_phone'],
            user_info['fo_user_addr'],
            user_info['user_agent'],
        ):
            raise ValidationError('COUPON_ERR_USED_COUPON')

    return coupon

def get_user_info(conn, id_user):
    sql = ("select users_address.country_code || ' ' || address || '' || address2 as fo_user_addr,"
           "       calling_code || '' || phone_num as fo_user_phone"
           "  from users"
           "  left join users_address "
           "    on (users.id = users_address.users_id and users_address.addr_type in (%s,%s))"
           "  left join users_phone_num on (users.id = users_phone_num.users_id)"
           "  left join country_calling_code on (users_phone_num.country_num = country_calling_code.country_code)"
           " where users.id=%s")
    row = db_utils.query(conn, sql,
        [ADDR_TYPE.Both, ADDR_TYPE.Shipping, id_user])[0]
    row_dict = dict(zip(("fo_user_addr", "fo_user_phone"), row))
    return row_dict

def check_order_for_coupon(conn, coupon, all_order_items, groups):
    if len(all_order_items) == 0:
        raise ValidationError('COUPON_ERR_INVALID_ORDER')
    id_shops = get_coupon_shop_data(conn, coupon['id'])
    conds, operation, threshold = get_coupon_condition_data(conn, coupon['id'])

    if id_shops:
        order_items = [o for o in all_order_items if o['shop_id'] in id_shops]
    else:
        order_items = [o for o in all_order_items]
    order_items = [o_item for o_item in order_items
                    if order_item_match_cond(o_item,
                        conds, coupon['id_brand'], id_shops)]
    order_match = len(order_items) > 0
    if order_match and \
            len([m['id'] for m in conds
                 if m['id_type'] == COUPON_CONDITION_IDTYPE.GROUP]) > 0:
        order_match = \
            order_items_match_group(all_order_items, groups, conds, operation)

    if not order_match:
        raise ValidationError('COUPON_ERR_INVALID_COUPON')

    if threshold:
        if operation == COUPON_CONDITION_OPERATION.SUM_ITEMS:
            value = sum([o['quantity'] for o in order_items])
            if not match_comparison(threshold['comparison'],
                    threshold['threshold'], value):
                raise ValidationError('COUPON_ERR_INVALID_COUPON')
        elif operation == COUPON_CONDITION_OPERATION.SUM_PRICE:
            value = sum([o['price'] * o['quantity'] for o in order_items])
            if not match_comparison(threshold['comparison'],
                    threshold['threshold'], value):
                raise ValidationError('COUPON_ERR_INVALID_COUPON')
    return order_items

def apply_appliable_coupons(conn, id_user, id_order, user_info):
    fields, columns = zip(*COUPON_FIELDS_COLUMNS)
    results = db_utils.query(conn, """
    select %s from coupons
    where password = '' and valid
      and (expiration_time is null or expiration_time > now())
      and (exists (
        select 1 from coupon_given_to where id_coupon=coupons.id and id_user=%%s
      ) or not exists (
        select 1 from coupon_given_to where id_coupon=coupons.id
      ))
      and coupon_type = %%s
    order by expiration_time, creation_time
    """ % ','.join(columns), [id_user, COUPON_REWARD_TYPE.COUPON_CURRENCY])
    credit_coupons = [dict(zip(fields, result)) for result in results]

    results = db_utils.query(conn, """
    select %s from coupons
    where password = '' and valid
      and (expiration_time is null or expiration_time > now())
      and (exists (
        select 1 from coupon_given_to where id_coupon=coupons.id and id_user=%%s
      ) or not exists (
        select 1 from coupon_given_to where id_coupon=coupons.id
      ))
      and coupon_type != %%s
    order by expiration_time, creation_time
    """ % ','.join(columns), [id_user, COUPON_REWARD_TYPE.COUPON_CURRENCY])
    other_coupons = [dict(zip(fields, result)) for result in results]

    appliable_coupons = []
    for coupon in other_coupons + credit_coupons:
        if len(appliable_coupons) > 0 and not coupon['stackable']:
            continue
        if coupon['max_redeemable'] and \
                _get_redeemed_times(conn, coupon['id']) >= coupon['max_redeemable']:
            continue
        if coupon['first_order_only'] and _user_having_orders(conn, id_user):
            continue
        if not coupon['redeemable_always']:
            user_info = get_user_info(conn, id_user)
            if _once_coupon_limited(conn, coupon['id'], id_user,
                user_info['fo_user_phone'],
                user_info['fo_user_addr'],
                user_info['user_agent'],
            ):
                continue

        all_order_items = get_order_items(conn, id_order)
        groups = get_promotion_groups(conn, coupon['id_brand'])
        try:
            match_order_items = \
                check_order_for_coupon(conn, coupon, all_order_items, groups)
        except ValidationError, e:
            continue

        reward_type = coupon['coupon_type']
        if reward_type == COUPON_REWARD_TYPE.COUPON_CURRENCY:
            try:
                credit_amount, currency = _calc_currency_credit(
                    conn, coupon['id'], coupon,
                    id_order, id_user, match_order_items)
            except ValidationError, e:
                continue

            db_utils.insert(conn, 'store_credit_redeemed', values={
                'id_coupon': coupon['id'],
                'id_user': id_user,
                'id_order': id_order,
                'order_status': ORDER_STATUS_FOR_COUPON.PENDING,
                'currency': currency,
                'redeemed_amount': credit_amount,
            })

        else:
            _calc_discount_result(conn, coupon['id'], coupon, id_order,
                                  all_order_items, match_order_items)

            db_utils.insert(conn, 'coupon_redeemed', values={
                'id_coupon': coupon['id'],
                'id_user': id_user,
                'id_order': id_order,
                'order_status': ORDER_STATUS_FOR_COUPON.PENDING,
                'account_address': user_info['fo_user_addr'],
                'account_phone': user_info['fo_user_phone'],
                'user_agent': user_info['user_agent'],
            })

        appliable_coupons.append(coupon)


def apply_password_coupon(conn, pwd_coupon, all_order_items, match_order_items,
                          id_user, id_order, user_info):
    assert pwd_coupon['coupon_type'] != COUPON_REWARD_TYPE.COUPON_CURRENCY
    _calc_discount_result(conn, pwd_coupon['id'], pwd_coupon, id_order,
                          all_order_items, match_order_items)

    db_utils.insert(conn, 'coupon_redeemed', values={
        'id_coupon': pwd_coupon['id'],
        'id_user': id_user,
        'id_order': id_order,
        'order_status': ORDER_STATUS_FOR_COUPON.PENDING,
        'account_address': user_info['fo_user_addr'],
        'account_phone': user_info['fo_user_phone'],
        'user_agent': user_info['user_agent'],
    })


def get_apply_before_coupons_taxes(conn, id_user, id_shop, id_sale):
    tax_list = []
    try:
        if id_shop:
            shop = ujson.loads(get_redis_cli().get(SHOP % id_shop))
            from_address = shop['address']
        else:
            sale = ujson.loads(get_redis_cli().get(SALE % id_sale))
            from_address = sale['brand']['address']

        to_address = get_user_address(conn, id_user,
                addr_type=ADDR_TYPE.Shipping)[0]

        taxes = tax_cache_proxy.get()
        for tax in taxes.values():
            if tax['applies_after_promos'] == 'True':
                continue
            if tax['country'] != from_address['country']['#text']:
                continue
            if tax.get('province') and \
                    tax['province'] != from_address['country']['@province']:
                continue
            if tax['shipping'].get('@country') and \
                    tax['shipping'].get('@country') != 'None' and \
                    tax['shipping'].get('@country') != to_address['country']:
                continue
            if tax['shipping'].get('@province') and \
                    tax['shipping'].get('@province') != to_address['province']:
                continue
            tax_list.append(tax)

    except Exception, e:
        logging.error("Failed to get apply-before-coupons taxes",
                      exc_info=True)
    return tax_list


def _calc_currency_credit(conn, id_coupon, coupon, id_order, id_user,
                          match_order_items):
    credit_value = db_utils.select_dict(
        conn, 'store_credit', 'id_coupon',
        where={'id_coupon': id_coupon}).values()[0]
    if credit_value['redeemed_in_full']:
        raise ValidationError('COUPON_ERR_REDEEMED_FULL')

    redeemed_amount = db_utils.query(conn,
        "select COALESCE(sum(redeemed_amount), 0) from store_credit_redeemed "
        "where id_coupon=%s and order_status in (%s, %s) ",
        [id_coupon,
         ORDER_STATUS_FOR_COUPON.PENDING,
         ORDER_STATUS_FOR_COUPON.PAID])[0][0]
    left_amount = credit_value['amount'] - redeemed_amount
    total_redeemable_amount = 0
    match_id_items = [item['item_id'] for item in match_order_items]

    shipments = get_shipments_by_order(conn, id_order)
    for shipment in shipments:
        if left_amount <= 0:
            continue
        shipping_list = get_shipping_list(conn, shipment['id'])
        price = sum([o['price'] * o['quantity']
                     for o in shipping_list
                     if o['id_item'] in match_id_items
                        and o['currency'] == credit_value['currency']])
        redeemed_amount = abs(
            sum([o['price'] * o['quantity']
                 for o in shipping_list
                 if o['id_sale'] == 0
                    and o['currency'] == credit_value['currency']]))

        taxes = get_apply_before_coupons_taxes(conn, id_user,
                shipment['id_shop'], shipping_list[0]['id_sale'])
        price_with_tax = price + sum(
                [(price + redeemed_amount) * float(tax['rate']) / 100.0
                 for tax in taxes])
        redeemable_amount = min(price_with_tax, left_amount)

        fake_item = {
            'id_sale': 0,
            'id_variant': 0,
            'id_brand': match_order_items[0]['brand_id'],
            'id_shop': match_order_items[0]['shop_id'],
            'name': '',
            'price': -min(price, left_amount),
            'currency': credit_value['currency'],
            'description': coupon['description'],
            'weight': 0,
            'weight_unit': match_order_items[0]['weight_unit'],
            'barcode': '',
            'external_id': '',
            'item_detail': ujson.dumps({
                'name': '',
                'redeemable_credits': redeemable_amount,
            }),
            'type_name': '',
            'modified_by_coupon': id_coupon,
        }
        _create_fake_order_item(conn, id_order, match_id_items[0], fake_item)
        left_amount -= redeemable_amount
        total_redeemable_amount += redeemable_amount

    return to_round(total_redeemable_amount), credit_value['currency']


def _calc_discount_result(conn, id_coupon, coupon, id_order,
                          all_order_items, match_order_items):
    results = db_utils.select_dict(
        conn, 'coupon_discount', 'id_coupon',
        where={'id_coupon': id_coupon}).values()
    if results:
        discount_value = results[0]
        if discount_value['discount_type'] == COUPON_DISCOUNT_APPLIES.VALUE_CHEAPEST:
            min_price_item = min_price = match_order_items[0]
            for o_item in match_order_items[1:]:
                if 0 < o_item['price'] < min_price_item['price']:
                    min_price_item = o_item
            for o_item in all_order_items:
                if o_item == min_price_item:
                    o_item['discount'] = _calc_discount(
                        o_item['price'], discount_value['discount'])
                    break

        elif discount_value['discount_type'] == COUPON_DISCOUNT_APPLIES.VALUE_MATCHING:
            for o_item in all_order_items:
                if o_item in match_order_items and o_item['price'] > 0:
                    o_item['discount'] = _calc_discount(
                        o_item['price'], discount_value['discount'])

        elif discount_value['discount_type'] == COUPON_DISCOUNT_APPLIES.VALUE_INVOICED:
            for o_item in all_order_items:
                o_item['discount'] = _calc_discount(
                    o_item['price'], discount_value['discount'])

        elif discount_value['discount_type'] == COUPON_DISCOUNT_APPLIES.VALUE_SHIPPING:
            shipments = get_shipments_by_order(conn, id_order)
            for shipment in shipments:
                fee = get_shipping_fee(conn, shipment['id'])
                update_values = {
                    'shipping_fee': 0,
                    'handling_fee': 0,
                    'details': ujson.dumps({
                        'free_fee': True,
                        'shipping_fee': fee['shipping_fee'] or 0,
                        'handling_fee': fee['handling_fee'] or 0,
                        'manufacturer_promo': coupon['manufacturer'],
                    })
                }
                update_shipping_fee(conn, shipment['id'], update_values)

        for o_item in all_order_items:
            if 'discount' not in o_item:
                continue
            _copy_fake_order_item(conn, id_order, o_item['item_id'], {
                'price': -o_item['discount'],
                'description': coupon['description'],
                'weight': 0,
                'barcode': '',
                'external_id': '',
                'name': '',
                'item_detail': '{"name": ""}',
                'type_name': '',
                'modified_by_coupon': id_coupon,
            }, quantity=o_item['quantity'])

    else:
        gift_values = db_utils.select(
            conn, 'coupon_gift', columns=('id_sale', 'quantity'),
            where={'id_coupon': id_coupon})
        if gift_values:
            for gift in gift_values:
                _create_free_order_item(conn, id_order, gift['id_sale'],
                    match_order_items[0]['item_id'],
                    {'price': 0, 'modified_by_coupon': id_coupon},
                    quantity=gift['quantity'])


def _create_fake_order_item(conn, id_order, orig_id_item,
                            item_value, quantity=1):
    id_item = db_utils.insert(conn, 'order_items',
                     values=item_value, returning='id')[0]
    logging.info('order_item create: item id: %s, values: %s',
                 id_item, item_value)
    details_value = {
        'id_order': id_order,
        'id_item': id_item,
        'quantity': quantity
    }
    db_utils.insert(conn, 'order_details', values=details_value)
    logging.info('order_details create: %s', details_value)

    _create_shipping_list(conn, id_item, orig_id_item, quantity=quantity)


def _copy_fake_order_item(conn, id_order, orig_id_item,
                          item_update_value, quantity=1):
    item_copy_value = db_utils.select_dict(
        conn, 'order_items', 'id',
        where={'id': orig_id_item}).values()[0]
    item_copy_value = dict(item_copy_value)
    item_copy_value.update(item_update_value)
    item_copy_value.pop('id')

    id_item = db_utils.insert(conn, 'order_items',
                     values=item_copy_value, returning='id')[0]
    logging.info('order_item create: item id: %s, values: %s',
                 id_item, item_copy_value)
    details_value = {
        'id_order': id_order,
        'id_item': id_item,
        'quantity': quantity
    }
    db_utils.insert(conn, 'order_details', values=details_value)
    logging.info('order_details create: %s', details_value)

    db_utils.update(conn, "order_items",
                    values={'modified_by_coupon':
                        item_copy_value['modified_by_coupon']},
                    where={'id': orig_id_item})

    _create_shipping_list(conn, id_item, orig_id_item, quantity=quantity)


def _create_free_order_item(conn, id_order, id_sale, orig_id_item,
                            item_update_value, quantity=1):
    sale = CachedSale(id_sale).sale
    id_item = _create_order_item(conn, sale, 0, sale.brand.id)
    db_utils.update(conn, "order_items",
        values=item_update_value, where={'id': id_item})
    _create_order_details(conn, id_order, id_item, quantity)
    _create_shipping_list(conn, id_item, orig_id_item, quantity=quantity)


def _create_shipping_list(conn, id_item, orig_id_item, quantity=1):
    shipping_value = db_utils.select_dict(
        conn, 'shipping_list', 'id',
        where={'id_item': orig_id_item}).values()[0]

    db_utils.insert(conn, 'shipping_list', values={
        'id_item': id_item,
        'id_shipment': shipping_value['id_shipment'],
        'quantity': quantity,
        'packing_quantity': quantity,
        'free_shipping': shipping_value['free_shipping'],
    })


def _calc_discount(price, discount):
    return to_round(price * discount * 0.01)


def _get_redeemed_times(conn, id_coupon):
    results = db_utils.query(conn,
        "select id from coupon_redeemed "
        "where id_coupon=%s and order_status in (%s, %s) "
        "union "
        "select id from store_credit_redeemed "
        "where id_coupon=%s and order_status in (%s, %s) ",
        [id_coupon,
         ORDER_STATUS_FOR_COUPON.PENDING,
         ORDER_STATUS_FOR_COUPON.PAID] * 2)
    return len(results)


def _user_having_orders(conn, id_user):
    results = db_utils.query(conn,
        "select id from orders where id_user=%s and valid limit 5",
        [id_user])
    return len(results) > 1 # don't count in the current order


def _once_coupon_limited(conn, id_coupon, id_users,
                         fo_user_phone, fo_user_addr, user_agent):
    same_user_cond = """
        id_user=%s or account_phone=%s or account_address=%s or user_agent=%s
    """
    params = [
        id_coupon,
        ORDER_STATUS_FOR_COUPON.PENDING,
        ORDER_STATUS_FOR_COUPON.PAID,
        id_users,
        fo_user_phone,
        fo_user_addr
    ]
    if user_agent:
        params.append(user_agent)
    results = db_utils.query(conn,
        "select id from coupon_redeemed "
        "where id_coupon=%%s and order_status in (%%s, %%s) "
        "and (%s) "
        "union "
        "select id from store_credit_redeemed "
        "where id_coupon=%%s and order_status in (%%s, %%s) "
        "and (%s) " % (same_user_cond, same_user_conf),
        params * 2)
    return len(results) > 0


def cancel_coupon_for_order(conn, id_order):
    db_utils.update(conn, 'coupon_redeemed',
                    values={'order_status': ORDER_STATUS_FOR_COUPON.CANCELLED},
                    where={'id_order': id_order})
    db_utils.update(conn, 'store_credit_redeemed',
                    values={'order_status': ORDER_STATUS_FOR_COUPON.CANCELLED},
                    where={'id_order': id_order})

    id_coupons = [item['modified_by_coupon']
                  for item in get_order_items(conn, id_order)
                  if item['modified_by_coupon']]
    for id_coupon in id_coupons:
        # check if need to mark redeemed_in_full False
        credit_value = _get_store_credit(conn, id_coupon)
        redeemed_amount = _get_store_redeemed_amount(conn, id_coupon)
        if credit_value and credit_value['amount'] > to_round(redeemed_amount):
            db_utils.update(conn, 'store_credit',
                            values={'redeemed_in_full': False},
                            where={'id_coupon': id_coupon})


def redeem_coupon_for_shipment(conn, id_order, id_shipment, id_invoice):
    shipping_list = get_shipping_list(conn, id_shipment)
    coupon_items = [item for item in shipping_list
                    if item['modified_by_coupon']]
    items_group_by_coupon = {}
    for item in shipping_list:
        if not item['modified_by_coupon'] or item['price'] > 0:
            continue
        if item['modified_by_coupon'] not in items_group_by_coupon:
            items_group_by_coupon[item['modified_by_coupon']] = []
        items_group_by_coupon[item['modified_by_coupon']].append(item)

    for id_coupon, items in items_group_by_coupon.iteritems():
        _coupon_redeemed(conn, id_coupon, id_order, id_invoice)
        amount = to_round(sum([item['quantity'] * item['price']
                               for item in items]))
        _store_credit_redeemed(conn, id_coupon, id_order, id_invoice, amount)


def _coupon_redeemed(conn, id_coupon, id_order, id_invoice):
    results = db_utils.select(
        conn, 'coupon_redeemed',
        where={
            'id_coupon': id_coupon,
            'id_order': id_order,
        })
    if not results:
        return

    update_values = {
        'id_invoice': id_invoice,
        'order_status': ORDER_STATUS_FOR_COUPON.PAID,
    }
    if len(results) == 1 and results[0]['id_invoice'] is None:
        db_utils.update(conn, 'coupon_redeemed',
                        values=update_values,
                        where={'id': results[0]['id']})
    else:
        values = {
            'id_coupon': results[0]['id_coupon'],
            'id_user': results[0]['id_user'],
            'id_order': results[0]['id_order'],
            'redeemed_time': results[0]['redeemed_item'],
            'account_address': results[0]['account_address'],
            'account_phone': results[0]['account_phone'],
            'user_agent': results[0]['user_agent'],
        }
        values.update(update_values)
        db_utils.insert(conn, 'coupon_redeemed', values=values)


def _store_credit_redeemed(conn, id_coupon, id_order, id_invoice, amount):
    results = db_utils.select(
        conn, 'store_credit_redeemed',
        where={
            'id_coupon': id_coupon,
            'id_order': id_order,
        },
        order=('-id_invoice',))
    if not results or results[0]['id_invoice']:
        return

    update_values = {
        'id_invoice': id_invoice,
        'order_status': ORDER_STATUS_FOR_COUPON.PAID,
    }
    total = to_round(results[0]['redeemed_amount'])
    if total <= amount:
        db_utils.update(conn, 'store_credit_redeemed',
                        values=update_values,
                        where={'id': results[0]['id']})
    else:
        values = {
            'id_coupon': results[0]['id_coupon'],
            'id_user': results[0]['id_user'],
            'id_order': results[0]['id_order'],
            'currency': results[0]['currency'],
            'redeemed_amount': amount,
        }
        values.update(update_values)
        db_utils.insert(conn, 'store_credit_redeemed', values=values)

        db_utils.update(conn, 'store_credit_redeemed',
                        values={'redeemed_amount': to_round(total - amount)},
                        where={'id': results[0]['id']})

    # check if need to mark redeemed_in_full
    credit_value = _get_store_credit(conn, id_coupon)
    redeemed_amount = _get_store_redeemed_amount(conn, id_coupon)
    if credit_value and credit_value['amount'] <= to_round(redeemed_amount):
        db_utils.update(conn, 'store_credit',
                        values={'redeemed_in_full': True},
                        where={'id_coupon': id_coupon})


def _get_store_credit(conn, id_coupon):
    results = db_utils.select(
        conn, 'store_credit', where={'id_coupon': id_coupon})
    return results[0] if results else None


def _get_store_redeemed_amount(conn, id_coupon):
    return db_utils.query(conn,
        "select COALESCE(sum(redeemed_amount), 0) from store_credit_redeemed "
        "where id_coupon=%s and order_status = %s ",
        [id_coupon, ORDER_STATUS_FOR_COUPON.PAID])[0][0]


def get_promotion_groups(conn, id_brand, id_shop=None):
    return group_cache_proxy.get(seller=id_brand, shop=id_shop)
