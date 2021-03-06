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


import cgi
from datetime import datetime
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import SHOP
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from common.cache import shop_cache_proxy
from common.constants import COUPON_CONDITION_IDTYPE
from common.constants import COUPON_CONDITION_OPERATION
from common.constants import COUPON_CONDITION_COMPARISON
from common.constants import COUPON_DISCOUNT_APPLIES
from common.constants import COUPON_REWARD_TYPE
from common.constants import ORDER_STATUS_FOR_COUPON
from common.redis_utils import get_redis_cli
from common.utils import to_unicode
from models.coupon import apply_password_coupon
from models.coupon import check_coupon_with_password
from models.coupon import check_order_for_coupon
from models.coupon import get_coupon_condition_data
from models.coupon import get_coupon_shop_data
from models.coupon import get_coupon_user_data
from models.coupon import get_promotion_groups
from models.coupon import get_user_info
from models.coupon import match_comparison
from models.coupon import order_item_match_cond
from models.order import get_order_items
from webservice.base import BaseJsonResource
from webservice.base import BaseXmlResource


class CouponListResource(BaseXmlResource):
    template = "coupons.xml"
    encrypt = True
    service = SERVICES.ADM

    def _on_get(self, req, resp, conn, **kwargs):
        id_brand = req.get_param('id_brand')
        if not id_brand:
            raise ValidationError('COUPON_ERR_INVALID_ID_BRAND')

        params = cgi.parse_qs(req.query_string)
        id_shops = params.get('id_shop') or []

        id_item = req.get_param('id_item')
        id_promotion_group = req.get_param('promotion_group')
        id_product_brand = req.get_param('item_brand')

        query = """
            select id from coupons
            where id_brand=%s and valid
              and (expiration_time is null or expiration_time >= now())
            order by creation_time
        """
        id_coupons = db_utils.query(conn, query, [id_brand])
        id_coupons = [v[0] for v in id_coupons]
        if id_shops:
            id_coupons = self._filter_by_shops(conn, id_brand, id_shops, id_coupons)
        if id_item:
            id_coupons = self._filter_by_id(conn, COUPON_CONDITION_IDTYPE.SALE,
                                            id_item, id_coupons)
        if id_product_brand:
            id_coupons = self._filter_by_id(conn, COUPON_CONDITION_IDTYPE.BRAND,
                                            id_product_brand, id_coupons)
        if id_promotion_group:
            id_coupons = self._filter_by_id(conn, COUPON_CONDITION_IDTYPE.GROUP,
                                            id_promotion_group, id_coupons)

        data = []
        for id_coupon in id_coupons:
            c_values = db_utils.select_dict(
                conn, 'coupons', 'id', where={'id': id_coupon}).values()[0]
            coupon_data = {
                'id': c_values['id'],
                'issuer': c_values['id_brand'],
                'stackable': 'true' if c_values['stackable'] else 'false',
                'author': c_values['id_bo_user'],
                'coupon_type': COUPON_REWARD_TYPE.toReverseDict().get(
                               c_values['coupon_type']),
                'desc': c_values['description'],
                'password': c_values['password'],
                'effective_time': str(c_values['effective_time'])[:19],
                'expiration_time': str(c_values['expiration_time'] or '')[:19],
                'redeemable_always':
                    'true' if c_values['redeemable_always'] else 'false',
                'max_redeemable': c_values['max_redeemable'] or '',
            }

            coupon_data.update({
                'id_users': get_coupon_user_data(conn, id_coupon),
            })
            coupon_data.update({
                'shops': [self._get_shop_details(id_shop)
                    for id_shop in get_coupon_shop_data(conn, id_coupon)]
            })
            conds, operation, threshold = get_coupon_condition_data(conn, id_coupon)
            require = {}
            if operation:
                require['operation'] = \
                        COUPON_CONDITION_OPERATION.toReverseDict()[operation]
            if threshold:
                require.update(threshold)
            if conds:
                require['match'] = conds
            if require:
                require.update({
                    'order': 'first' if c_values['first_order_only'] else 'any',
                })
                coupon_data['require'] = require

            reward = self._get_reward_data(conn, id_coupon,
                                         c_values['coupon_type'])
            coupon_data['reward'] = reward

            data.append(coupon_data)
        return {'coupons': to_unicode(data)}

    def _filter_by_shops(self, conn, id_brand, id_shops, id_coupons):
        query = """select id from coupons
        where id_brand=%s and not exists (
            select 1 from coupon_accepted_at where id_coupon = coupons.id)
        union
        select id_coupon from coupon_accepted_at where id_shop in (%s)
        union
        select id_coupon from coupon_condition where id_value in (%s) and id_type= %s
        """ % (id_brand, ','.join(id_shops), ','.join(id_shops),
               COUPON_CONDITION_IDTYPE.SHOP)
        results = db_utils.query(conn, query)
        results = [v[0] for v in results]
        if results:
            results = list(set(id_coupons).intersection(results))
            results.sort(key=lambda o:id_coupons.index(o))
            return results
        else:
            return id_coupons

    def _filter_by_id(self, conn, id_type, id_value, id_coupons):
        results = db_utils.select(
            conn, 'coupon_condition', columns=('id_coupon',),
            where={'id_value': id_value,
                   'id_type': id_type})
        results = [v[0] for v in results]
        if results:
            results = list(set(id_coupons).intersection(results))
            results.sort(key=lambda o:id_coupons.index(o))
            return results
        else:
            return id_coupons

    def _get_shop_details(self, id_shop):
        shop = get_redis_cli().get(SHOP % id_shop)
        if not shop:
            shop = {'@id': id_shop}
            logging.error('Missing shop info(id=%s) in redis', id_shop)
        return ujson.loads(shop)

    def _get_reward_data(self, conn, id_coupon, coupon_type):
        reward = {}
        if coupon_type == COUPON_REWARD_TYPE.COUPON_CURRENCY:
            credit_value = db_utils.select_dict(
                conn, 'store_credit', 'id_coupon',
                where={'id_coupon': id_coupon}).values()[0]
            reward['credit'] = {
                'currency': credit_value['currency'],
                'amount': credit_value['amount'],
            }
        else:
            gift_values = db_utils.select(
                conn, 'coupon_gift', columns=('id_sale', 'quantity'),
                where={'id_coupon': id_coupon})
            if gift_values:
                reward['gifts'] = [{'item_id': gift[0], 'quantity': gift[1]}
                                   for gift in gift_values]
                results = db_utils.select(
                    conn, 'coupon_give_away', where={'id_coupon': id_coupon})
                if results:
                    reward['max_selection'] = results[0]['max_selection'] or 0
            else:
                discount_value = db_utils.select_dict(
                    conn, 'coupon_discount', 'id_coupon',
                    where={'id_coupon': id_coupon}).values()[0]
                reward['discount'] = {
                    'type': COUPON_DISCOUNT_APPLIES.toReverseDict()[
                            discount_value['discount_type']],
                    'discount': discount_value['discount'],
                }
        return reward


class CouponPostResource(BaseXmlResource):
    template = "coupon_create.xml"
    encrypt = True
    service = SERVICES.ADM

    post_action_func_map = {
        'create': 'coupon_create',
        'update': 'coupon_update',
        'delete': 'coupon_delete',
    }

    def _on_post(self, req, resp, conn, **kwargs):
        action = req.get_param('action')
        if action is None or action not in self.post_action_func_map:
            logging.error('Invalid Coupon post: %s', req.query_string)
            raise ValidationError('COUPON_ERR_INVALID_ACTION')
        func = getattr(self, self.post_action_func_map[action], None)
        assert hasattr(func, '__call__')
        return func(req, resp, conn)

    def coupon_create(self, req, resp, conn, id_coupon=None):
        is_edit = id_coupon is not None

        try:
            id_brand = req.get_param('id_issuer')
            assert id_brand, 'id_issuer'
            id_bo_user = req.get_param('author')
            assert id_bo_user, 'author'

            id_users = req.get_param('beneficiary')
            if id_users:
                try:
                    id_users = [int(id_) for id_ in id_users.split(',')]
                except ValueError, e:
                    raise ValidationError('COUPON_ERR_INVALID_PARAM_beneficiary')

            id_shops = req.get_param('participating')
            if id_shops:
                try:
                    id_shops = [int(id_) for id_ in id_shops.split(',')]
                except ValueError, e:
                    raise ValidationError('COUPON_ERR_INVALID_PARAM_participating')

            effective_time = req.get_param('effective_time')
            if effective_time is not None:
                try:
                    effective_time = datetime.strptime(effective_time,
                                                      "%Y-%m-%d %H:%M:%S")
                except ValueError, e:
                    try:
                        effective_time = datetime.strptime(effective_time,
                                                          "%Y-%m-%d")
                        effective_time = datetime.combine(effective_time,
                                                         datetime.min.time())
                    except ValueError, e:
                        raise ValidationError('COUPON_ERR_INVALID_PARAM_effective_time')

            expiration_time = req.get_param('expiration_time')
            if expiration_time is not None:
                try:
                    expiration_time = datetime.strptime(expiration_time,
                                                        "%Y-%m-%d %H:%M:%S")
                except ValueError, e:
                    try:
                        expiration_time = datetime.strptime(expiration_time,
                                                            "%Y-%m-%d")
                        expiration_time = datetime.combine(expiration_time,
                                                           datetime.max.time())
                    except ValueError, e:
                        raise ValidationError('COUPON_ERR_INVALID_PARAM_expiration_time')

            password = req.get_param('password') or ''
            if password and not is_edit:
                results = db_utils.select(
                    conn, 'coupons', columns=('id',),
                    where={'password': password, 'valid': True})
                if len(results) > 0:
                    raise ValidationError('COUPON_ERR_INVALID_PARAM_password')

            redeemable_always = True
            if req.get_param('redeemable') and \
                    req.get_param('redeemable') == 'once':
                redeemable_always = False
            max_redeem = req.get_param('max_redeem')
            if max_redeem:
                max_redeem = int(max_redeem)
            coupon_values = {
                'id_brand': id_brand,
                'id_bo_user': id_bo_user,
                'expiration_time': expiration_time,
                'stackable': req.get_param('stackable') in ('True', 'true'),
                'redeemable_always': redeemable_always,
                'first_order_only': req.get_param('first_order_only')
                                    in ('True', 'true'),
                'password': password,
                'description': req.get_param('description') or '',
                'valid': True,
            }
            if effective_time:
                coupon_values.update({'effective_time': effective_time})
            if max_redeem:
                coupon_values.update({'max_redeemable': max_redeem})

            require = req.get_param('require') or '{}'
            require = ujson.loads(require)
            if require:
                cond_list = self._check_coupon_require(require)

            reward_type = req.get_param('reward_type')
            assert reward_type and hasattr(COUPON_REWARD_TYPE, reward_type), 'reward_type'
            reward_type = getattr(COUPON_REWARD_TYPE, reward_type)
            coupon_values.update({'coupon_type': reward_type})

            if reward_type == COUPON_REWARD_TYPE.COUPON_CURRENCY:
                coupon_values.update({'stackable': True})
                store_credit_values = self._get_coupon_reward_currency(req)
            else:
                discount_values, gift_values = \
                    self._get_coupon_reward_discount(req, require, reward_type)

        except AssertionError, e:
            logging.error('Invalid Coupon request: %s', req.query_string)
            raise ValidationError('COUPON_ERR_INVALID_PARAM_%s' % e)


        if is_edit:
            db_utils.update(conn, 'coupons',
                            values=coupon_values,
                            where={'id': id_coupon})
        else:
            id_coupon = db_utils.insert(conn, 'coupons',
                                        values=coupon_values,
                                        returning='id')[0]

        if is_edit:
            for table in (
                'coupon_given_to', 'coupon_accepted_at', 'coupon_condition',
                'store_credit', 'coupon_discount', 'coupon_give_away',
                'coupon_gift'):
                db_utils.delete(conn, table,
                                where={'id_coupon': id_coupon})

        if id_users:
            for id_user in id_users:
                db_utils.insert(conn, 'coupon_given_to',
                                values={'id_coupon': id_coupon,
                                        'id_user': id_user})
        if id_shops:
            for id_shop in id_shops:
                db_utils.insert(conn, 'coupon_accepted_at',
                                values={'id_coupon': id_coupon,
                                        'id_shop': id_shop})

        if require and cond_list:
            for cond_values in cond_list:
                cond_values.update({'id_coupon': id_coupon})
                db_utils.insert(conn, 'coupon_condition',
                                values=cond_values)

        if reward_type == COUPON_REWARD_TYPE.COUPON_CURRENCY:
            store_credit_values.update({'id_coupon': id_coupon})
            db_utils.insert(conn, 'store_credit',
                            values=store_credit_values)
        else:
            if discount_values:
                discount_values.update({'id_coupon': id_coupon})
                db_utils.insert(conn, 'coupon_discount',
                                values=discount_values)
            if gift_values:
                for g_values in gift_values.pop('list'):
                    g_values.update({'id_coupon': id_coupon})
                    db_utils.insert(conn, 'coupon_gift',
                                    values=g_values)
                if gift_values:
                    gift_values.update({'id_coupon': id_coupon})
                    db_utils.insert(conn, 'coupon_give_away',
                                    values=gift_values)

        return {'id_coupon': id_coupon}

    def _check_coupon_require(self, require):
        try:
            assert require.get('invoice_match'), 'invoice_match'
            params = require['invoice_match']
            if params.get('sale'):
                assert all([isinstance(id_, int) for id_ in params['sale']]),\
                       'sale'
            if params.get('shop'):
                assert all([isinstance(id_, int) for id_ in params['shop']]),\
                       'shop'
            if params.get('brand'):
                assert all([isinstance(id_, int) for id_ in params['brand']]),\
                       'brand'
            if params.get('promotion_group'):
                assert all([isinstance(id_, int)
                            for id_ in params['promotion_group']]),\
                       'promotion_group'
            id_sales = params.get('sale') or []
            id_shops = params.get('shop') or []
            id_product_brands = params.get('brand') or []
            id_promotion_groups = params.get('promotion_group') or []

            operation = params.get('operation') or 'NONE'
            assert hasattr(COUPON_CONDITION_OPERATION, operation), 'operation'
            operation = getattr(COUPON_CONDITION_OPERATION, operation)
            more_than = params.get('more_than')
            less_than = params.get('less_than')
            equal = params.get('equal')
            if more_than is not None:
                assert less_than is None, 'more_than'
                threshold = float(more_than)
                if equal is not None and more_than == equal:
                    comparison = COUPON_CONDITION_COMPARISON.GTE
                else:
                    comparison = COUPON_CONDITION_COMPARISON.GT
            elif less_than is not None:
                threshold = float(less_than)
                if equal is not None and less_than == equal:
                    comparison = COUPON_CONDITION_COMPARISON.LTE
                else:
                    comparison = COUPON_CONDITION_COMPARISON.LT
            elif equal is not None:
                threshold = float(equal)
                comparison = COUPON_CONDITION_COMPARISON.EQ
            else:
                assert operation not in (
                    COUPON_CONDITION_OPERATION.SUM_ITEMS,
                    COUPON_CONDITION_OPERATION.SUM_PRICE), 'operation'

            cond_value = {'operation': operation}
            if operation in (COUPON_CONDITION_OPERATION.SUM_ITEMS,
                             COUPON_CONDITION_OPERATION.SUM_PRICE):
                cond_value.update({
                    'comparison': comparison,
                    'threshold': threshold,
                })

            cond_list = self._get_cond_values(COUPON_CONDITION_IDTYPE.SALE,
                                              id_sales, cond_value) + \
                self._get_cond_values(COUPON_CONDITION_IDTYPE.SHOP,
                                      id_shops, cond_value) + \
                self._get_cond_values(COUPON_CONDITION_IDTYPE.BRAND,
                                      id_product_brands, cond_value) + \
                self._get_cond_values(COUPON_CONDITION_IDTYPE.GROUP,
                                      id_promotion_groups, cond_value)
            if cond_value and len(cond_list) == 0:
                cond_list.append(cond_value)
            return cond_list

        except AssertionError, e:
            raise ValidationError('COUPON_ERR_REQUIRE_INVALID_PARAM_%s' % e)

    def _get_cond_values(self, id_type, ids, values):
        cond_list = []
        for id_ in ids:
            v = values.copy()
            v.update({
                'id_value': id_,
                'id_type': id_type,
            })
            cond_list.append(v)
        return cond_list

    def _get_coupon_reward_currency(self, req):
        store_credit_amount = req.get_param('store_credit_amount')
        assert store_credit_amount, 'store_credit_amount'
        try:
            store_credit_amount = float(store_credit_amount)
        except ValueError, e:
            raise ValidationError('COUPON_ERR_INVALID_PARAM_store_credit_amount')

        store_credit_currency = req.get_param('store_credit_currency')
        assert store_credit_currency, 'store_credit_currency'

        return {
            'currency': store_credit_currency,
            'amount': store_credit_amount,
        }

    def _get_coupon_reward_discount(self, req, require, reward_type):
        discount_values = {}
        gift_values = {}
        if req.get_param('gift'):
            gifts = ujson.loads(req.get_param('gift', '[]'))
            assert isinstance(gifts, list), 'gift'
            for gift in gifts:
                assert 'id' in gift and isinstance(gift['id'], int), 'gift'
                assert ('quantity' in gift and
                         isinstance(gift['quantity'], int)), 'gift'
            gift_values.update({'list': [{'id_sale': gift['id'],
                                          'quantity': gift['quantity']}
                                          for gift in gifts]})
            if req.get_param('select_only'):
                max_selection = req.get_param('select_only')
                assert 0 < int(req.get_param('select_only')) <= len(gifts), \
                       'select_only'
                gift_values.update({'max_selection': req.get_param('select_only')})
        else:
            discount_applies_to = req.get_param('discount_applies_to')
            assert discount_applies_to and \
                   hasattr(COUPON_DISCOUNT_APPLIES, discount_applies_to), \
                   'discount_applies_to'
            discount_applies_to = getattr(COUPON_DISCOUNT_APPLIES, discount_applies_to)
            if not require and discount_applies_to in (
                    COUPON_DISCOUNT_APPLIES.VALUE_MATCHING,
                    COUPON_DISCOUNT_APPLIES.VALUE_CHEAPEST
                ):
                raise AssertionError('discount_applies_to')

            if reward_type == COUPON_REWARD_TYPE.COUPON_DISCOUNT:
                assert (discount_applies_to !=
                        COUPON_DISCOUNT_APPLIES.VALUE_SHIPPING),\
                       'discount_applies_to'
                discount = req.get_param('discount')
                assert discount, 'discount'
                discount = float(discount)

            elif reward_type == COUPON_REWARD_TYPE.COUPON_GIVEAWAY:
                discount = 100
            discount_values.update({
               'discount_type': discount_applies_to,
               'discount': discount,
            })
        return discount_values, gift_values

    def coupon_update(self, req, resp, conn):
        id_brand = req.get_param('id_issuer')
        if not id_brand:
            raise ValidationError('COUPON_ERR_INVALID_ID_BRAND')

        id_coupon = req.get_param('id_coupon')
        coupons = db_utils.select(
            conn, 'coupons', where={'id': id_coupon})
        if not coupons:
            raise ValidationError('COUPON_ERR_INVALID_ID_COUPON')
        if coupons[0]['id_brand'] != int(id_brand):
            raise ValidationError('COUPON_ERR_INVALID_COUPON_FOR_BRAND')

        return self.coupon_create(req, resp, conn, id_coupon=id_coupon)

    def coupon_delete(self, req, resp, conn):
        id_brand = req.get_param('id_issuer')
        if not id_brand:
            raise ValidationError('COUPON_ERR_INVALID_ID_BRAND')

        id_coupon = req.get_param('id_coupon')
        coupons = db_utils.select(
            conn, 'coupons', where={'id': id_coupon})
        if not coupons:
            raise ValidationError('COUPON_ERR_INVALID_ID_COUPON')
        if coupons[0]['id_brand'] != int(id_brand):
            raise ValidationError('COUPON_ERR_INVALID_COUPON_FOR_BRAND')

        db_utils.update(conn, 'coupons', values={'valid': False},
                        where={'id': id_coupon})
        return {'id_coupon': id_coupon}


class CouponRedeemResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}
    users_id = None

    def _on_post(self, req, resp, conn, **kwargs):
        self.users_id = kwargs.get('users_id')
        id_order = req.get_param('id_order')
        password = req.get_param('password')

        if not id_order:
            raise ValidationError('COUPON_ERR_INVALID_IDORDER')
        if not password:
            raise ValidationError('COUPON_ERR_INVALID_PASSWORD')
        user_info = get_user_info(conn, self.users_id)
        user_info['user_agent'] = req.get_header('User-Agent')
        coupon = check_coupon_with_password(
            conn, password, self.users_id, id_order, user_info)

        all_order_items = get_order_items(conn, id_order)
        groups = get_promotion_groups(conn, req.get_param('brand'))
        match_order_items = \
            check_order_for_coupon(conn, coupon, all_order_items, groups)
        chosen_gifts = ujson.loads(req.get_param('gifts') or '[]')
        apply_password_coupon(conn, coupon, all_order_items, match_order_items,
                              self.users_id, id_order, user_info, chosen_gifts)
        return {"res": RESP_RESULT.S, "err": ""}

