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


from common.redis_utils import get_redis_cli
from B2SProtocol.constants import SHOP_WITH_BARCODE
from B2SProtocol.constants import SHOP
from B2SUtils.base_actor import BaseActor
from B2SUtils.base_actor import as_list

def get_shop_id(upc_shop):
    cli = get_redis_cli()
    barcode_key = SHOP_WITH_BARCODE % upc_shop
    return cli.get(barcode_key)

def get_shop(upc_shop=None, id_shop=None):
    assert upc_shop or id_shop
    cli = get_redis_cli()
    if upc_shop:
        id_shop = get_shop_id(upc_shop)

    key = SHOP % id_shop
    shop = cli.get(key)
    return shop, key

class ActorBrand(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                'img': 'img'}
    @property
    def business(self):
        for reg in self.regs:
            if reg.type == 'business':
                return reg

    @property
    def tax(self):
        for reg in self.regs:
            if reg.type == 'tax':
                return reg

    @property
    def regs(self):
        regs_data = as_list(self.data['id'])
        return [Registration(data=item) for item in regs_data]

    @property
    def address(self):
        return Address(data=self.data['address'])


class Location(BaseActor):
    attrs_map = {'lat': '@lat',
                 'long': '@long'}

class Country(BaseActor):
    attrs_map = {'province': '@province',
                 'value': '#text'}

class Address(BaseActor):
    attrs_map = {
        'id': '@id',
        'addr': 'addr',
        'zip': 'zip',
        'city': 'city',
    }

    @property
    def country(self):
        return Country(data=self.data['country'])

class Registration(BaseActor):
    attrs_map = {'type': '@type',
                 'value': '#text'}


class ActorShop(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc',
                 'caption': 'caption',
                 'img': 'img',
                 'upc': 'upc',
                 'hours': 'hours',
                 }
    @property
    def business(self):
        for reg in self.regs:
            if reg.type == 'business':
                return reg

    @property
    def tax(self):
        for reg in self.regs:
            if reg.type == 'tax':
                return reg

    @property
    def regs(self):
        regs_data = as_list(self.data['id'])
        return [Registration(data=item) for item in regs_data]

    @property
    def address(self):
        return Address(data=self.data['address'])

    @property
    def brand(self):
        return ActorBrand(data=self.data['brand'])

    @property
    def localtion(self):
        return Location(data=self.data['location'])

class CachedShop:
    def __init__(self, upc_shop=None, id_shop=None):
        self._xml_shop, _ = get_shop(upc_shop, id_shop)
        self._shop = None

    @property
    def shop(self):
        if not self._xml_shop:
            return

        if self._shop is None:
            self._shop = ActorShop(xml_data=self._xml_shop)
        return self._shop

