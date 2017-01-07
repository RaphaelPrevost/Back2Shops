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


from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor


class ActorID(BaseActor):
    attrs_map = {
        'id': '#text',
        'type': '@type',
    }

class ActorUser(BaseActor):
    attrs_map = {
        'id': '#text',
    }

class ActorBrand(BaseActor):
    attrs_map = {
        'id': '@id',
        'name': 'name',
        'img': 'img',
    }

    @property
    def address(self):
        return ActorAddress(self.data.get('address'))

    @property
    def ids(self):
        data = as_list(self.data.get('id'))
        return [ActorID(data=u) for u in data]


class ActorCountry(BaseActor):
    attrs_map = {
        'province': '@province',
        'country': '#text',
    }

class ActorAddress(BaseActor):
    attrs_map = {
        'id': '@id',
        'addr': 'addr',
        'zip': 'zip',
        'city': 'city',
    }

    @property
    def country(self):
        return ActorCountry(self.data.get('country'))

class ActorLocation(BaseActor):
    attrs_map = {
        'lat': '@lat',
        'long': '@long',
    }

class ActorShop(BaseActor):
    attrs_map = {
        'id': '@id',
        'name': 'name',
        'desc': 'desc',
        'caption': 'caption',
        'img': 'img',
        'upc': 'upc',
        'hours': 'hours',
    }

    @property
    def brand(self):
        return ActorBrand(self.data.get('brand'))

    @property
    def address(self):
        return ActorAddress(self.data.get('address'))

    @property
    def location(self):
        return ActorLocation(self.data.get('location'))

    @property
    def ids(self):
        data = as_list(self.data.get('id'))
        return [ActorID(data=u) for u in data]

class ActorRedeemable(BaseActor):
    attrs_map = {
        'max': '@max',
        'always': '@always',
    }

    @property
    def users(self):
        data = as_list(self.data.get('beneficiary'))
        return [ActorUser(data=u) for u in data]

    @property
    def shops(self):
        data = as_list(self.data.get('shop'))
        return [ActorShop(data=s) for s in data]


class ActorThreshold(BaseActor):
    attrs_map = {
        'sum': '@sum',
        'comparison': '@must',
        'threshold': '#text',
    }

class ActorOrder(BaseActor):
    attrs_map = {
        'match': '@match',
        'match_id': '@id',
    }

class ActorRequire(BaseActor):
    @property
    def first_order(self):
        return self.data.get('order') == 'first'

    @property
    def order(self):
        order_data = as_list(self.data.get('order'))
        return [ActorOrder(data=o) for o in order_data]


class ActorGift(BaseActor):
    attrs_map = {
        'quantity': '@quantity',
        'id': '#text',
    }

class ActorRebate(BaseActor):
    attrs_map = {
        'type': '@type',
        'ratio': '#text',
    }

class ActorCredit(BaseActor):
    attrs_map = {
        'currency': '@currency',
        'amount': '#text',
    }

class ActorReward(BaseActor):

    @property
    def rebate(self):
        return ActorRebate(self.data.get('rebate', {}))

    @property
    def credit(self):
        return ActorCredit(self.data.get('credit'))

    @property
    def gift_max_selection(self):
        return self.data.get('gifts', {}).get('@max_selection')

    @property
    def gifts(self):
        gift_data = as_list(self.data.get('gifts', {}).get('gift'))
        return [ActorGift(data=g) for g in gift_data]


class ActorValid(BaseActor):
    attrs_map = {
        'from_': '@from',
        'to_': '@to',
    }

class ActorCoupon(BaseActor):
    attrs_map = {
        'id': '@id',
        'issuer': '@issuer',
        'stackable': '@stackable',
        'author': '@author',
        'type': 'type',
        'desc': 'desc',
        'password': 'password',
    }

    @property
    def valid(self):
        return ActorValid(data=self.data.get('valid'))

    @property
    def redeemable(self):
        return ActorRedeemable(data=self.data.get('redeemable'))

    @property
    def require(self):
        return ActorRequire(data=self.data.get('require'))

    @property
    def reward(self):
        return ActorReward(data=self.data.get('reward'))

class ActorCoupons(BaseActor):
    @property
    def coupons(self):
        coupons_data = as_list(self.data.get('coupons', {}).get('coupon'))
        return [ActorCoupon(data=c) for c in coupons_data]

