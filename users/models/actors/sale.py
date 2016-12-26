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
from datetime import datetime
from decimal import Decimal
from common.error import NotExistError
from common.redis_utils import get_redis_cli
from B2SProtocol.constants import SALE
from B2SProtocol.constants import BARCODE
from B2SProtocol.constants import BARCODE_VARIANT_ID
from B2SProtocol.constants import BARCODE_SALE_ID
from B2SUtils.base_actor import as_list
from B2SUtils.base_actor import BaseActor
from B2SUtils.common import to_round


class ActorProductBrand(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'img': 'img',
                 }

class ActorSaleCategory(BaseActor):
    attrs_map = {'id': '@id',
                 'default': '@default',
                 'name': 'name',
                 'img': 'img',
                 }

class ActorWeight(BaseActor):
    attrs_map = {'unit': '@unit',
                 'value': '#text'}

class ActorPrice(BaseActor):
    attrs_map = {'currency': '@currency',
                 'value': '#text'}


class ActorSaleCommonAttr(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def weight(self):
        wt = self.data.get('weight')
        if wt:
            return ActorWeight(data=wt)

    @property
    def price(self):
        pr = self.data.get('price')
        if pr:
            return ActorPrice(data=pr)

class ActorSaleVarAttr(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc'}

class ActorSaleType(BaseActor):
    attrs_map = {'id': '@id',
                 'default': '@default',
                 'name': 'name'}

    @property
    def attributes(self):
        attrs = as_list(self.data.get('attribute', None))
        return [ActorSaleCommonAttr(data=attr) for attr in attrs]

    @property
    def variable_attribute(self):
        attrs = as_list(self.data.get('variable_attribute', None))
        return [ActorSaleVarAttr(data=attr) for attr in attrs]

    def get_attr(self, id_attr):
        for attr in self.attributes:
            if int(id_attr) == int(attr.id):
                return attr

class ActorSaleCountry(BaseActor):
    attrs_map = {'province': '@province',
                 'value': '#text'}

class ActorAddress(BaseActor):
    attrs_map = {'id': '@id',
                 'addr': 'addr',
                 'city': 'city',
                 'zip': 'zip'}

    @property
    def country(self):
        return ActorSaleCountry(data=self.data['country'])

class ActorReg(BaseActor):
    attrs_map = {'type': '@type',
                 'value': '#text'}

class ActorSaleBrand(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'img': 'img'}

    @property
    def id_address(self):
        return self.address.id

    @property
    def address(self):
        return ActorAddress(data=self.data['address'])

    @property
    def regs(self):
        regs_data = as_list(self.data['id'])
        return [ActorReg(data=item) for item in regs_data]

    @property
    def business_reg(self):
        for reg in self.regs:
            if reg.type == 'business':
                return reg

    @property
    def tax_reg(self):
        for reg in self.regs:
            if reg.type == 'tax':
                return reg

class ActorSaleDiscount(BaseActor):
    attrs_map = {'type': '@type',
                 'from': '@from',
                 'to': '@to',
                 'text': '#text'}


class ActorSaleVariantPremium(BaseActor):
    attrs_map = {'type': '@type',
                 'text': '#text'}


class ActorSaleVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'thumb': 'thumb'}

    @property
    def img(self):
        return as_list(self.data.get('img', None))

    @property
    def premium(self):
        return ActorSaleVariantPremium(data=self.data.get('premium'))


class ActorShopLocaltion(BaseActor):
    attrs_map = {'lat': '@lat',
                 'long': '@long'}

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
    def localtion(self):
        return ActorShopLocaltion(data=self.data.get('location'))

    @property
    def id_address(self):
        return self.address.id

    @property
    def address(self):
        return ActorAddress(data=self.data['address'])

    @property
    def regs(self):
        regs_data = as_list(self.data['id'])
        return [ActorReg(data=item) for item in regs_data]

    @property
    def business_reg(self):
        for reg in self.regs:
            if reg.type == 'business':
                return reg

    @property
    def tax_reg(self):
        for reg in self.regs:
            if reg.type == 'tax':
                return reg

class ActorExternalRef(BaseActor):
    attrs_map = {'variant': '@variant',
                 'attribute': '@attribute',
                 'external_id': '#text'}

class ActorOrderConfirmSettings(BaseActor):
    attrs_map = {'default': '@default'}

    @property
    def requireconfirm(self):
        ll = as_list(self.data.get('requireconfirm', None))
        return [ActorRequireConfirm(data=s) for s in ll]

class ActorRequireConfirm(BaseActor):
    attrs_map = {'variant': '@variant',
                 'attribute': '@attribute',
                 'value': '#text'}

class ActorStock(BaseActor):
    attrs_map = {'shop': '@shop',
                 'alert': '@alert',
                 'available': '#text'}

class ActorStocks(BaseActor):
    attrs_map = {'variant': '@variant',
                 'attribute': '@attribute',
                 'upc': 'upc'}

    @property
    def stock(self):
        s_list = as_list(self.data.get('stock', None))
        return [ActorStock(data=s) for s in s_list]

class ActorSaleAvailable(BaseActor):
    attrs_map = {'from_': '@from',
                 'to_': '@to',
                 'total': '@total'}

    @property
    def stocks(self):
        stocks_list = as_list(self.data.get('stocks', None))
        return [ActorStocks(data=stock) for stock in stocks_list]

class ActorSale(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc',
                 'discount_price': 'discount_price',
                 }

    # attributes set/used in orders
    order_props = None
    shipping_setting = None

    def __repr__(self):
        return "ActorSale:%s" % '-'.join([unicode.encode(self.id, 'utf8'),
                                        unicode.encode(self.name, 'utf8'),
                                        unicode.encode(self.desc, 'utf8'),
                                        ])

    @property
    def product_brand(self):
        return ActorProductBrand(data=self.data['product_brand'])

    @property
    def category(self):
        return ActorSaleCategory(data=self.data['category'])

    @property
    def type(self):
        return ActorSaleType(data=self.data['type'])

    @property
    def img(self):
        return as_list(self.data.get('img', None))

    @property
    def brand(self):
        return ActorSaleBrand(data=self.data['brand'])

    @property
    def weight(self):
        return ActorWeight(data=self.data['weight'])

    @property
    def weight_unit(self):
        return self.weight.unit

    @property
    def standard_weight(self):
        return self.weight.value

    @property
    def price(self):
        return ActorPrice(data=self.data['price'])

    @property
    def discount(self):
        if self.data.get('discount'):
            return ActorSaleDiscount(data=self.data['discount'])

    @property
    def variant(self):
        variants = as_list(self.data.get('variant', None))
        return [ActorSaleVariant(data=variant) for variant in variants]

    @property
    def shops(self):
        shop_list = as_list(self.data.get('shop', None))
        return [ActorShop(data=item) for item in shop_list]

    @property
    def externals(self):
        external_list = as_list(self.data.get('external', None))
        return [ActorExternalRef(data=item) for item in external_list]

    @property
    def orderconfirmsettings(self):
        return ActorOrderConfirmSettings(data=self.data.get('orderconfirmsettings'))

    @property
    def available(self):
        return ActorSaleAvailable(data=self.data.get('available'))

    def available_now(self):
        def parse_date(date_str):
            return datetime.strptime(date_str[:10], '%Y-%m-%d').date()

        now = datetime.now().date()
        return (not self.available.from_
                or parse_date(self.available.from_) <= now) \
           and (not self.available.to_
                or parse_date(self.available.to_) >= now)

    def get_weight_attr(self, id_type):
        if id_type:
            return self.type.get_attr(id_type)

        raise NotExistError('weight for type %s not exist for Sale %s'
                            % (id_type, self.id))

    def get_type_price(self, id_type, raise_not_exist=True):
        if id_type:
            attr = self.type.get_attr(id_type)
            if attr and attr.price:
                return attr.price

        if raise_not_exist:
            raise NotExistError('price for type %s not exist for Sale %s'
                                % (id_type, self.id))

    def get_variant(self, id_variant):
        for v in self.variant:
            if int(id_variant) == int(v.id):
                return v
        raise NotExistError('Variant %s not exist for Sale %s'
                            % (id_variant, self.id))

    def get_shop(self, id_shop):
        for s in self.shops:
            if int(id_shop) == int(s.id):
                return s
        raise NotExistError('Shop%s not exist for Sale %s'
                            % (id_shop, self.id))

    def final_price(self, id_variant=0, id_price_type=0):
        def __diff_price(orig_price, obj):
            if obj is None:
                return 0

            if obj.type == 'ratio':
                return Decimal(orig_price) * Decimal(obj.text) / 100
            else:
                return Decimal(obj.text)

        def __base_price():
            if id_price_type and int(id_price_type):
                p = self.get_type_price(id_price_type,
                                        raise_not_exist=False)
            else:
                p = self.price

            return Decimal(p.value)

        price = Decimal(__base_price())
        if int(id_variant):
            v = self.get_variant(id_variant)
            premium = __diff_price(price, v.premium)
            price = price + premium
        return to_round(price)

    def whole_name(self, id_variant=0):
        name = self.name
        if int(id_variant):
            v = self.get_variant(id_variant)
            name = '-'.join([name, v.name])
        return name

    def get_external_id(self, id_variant, id_type):
        for ext in self.externals:
            if (id_variant and id_variant == ext.variant or not ext.variant) \
                    and (id_type and id_type == ext.attribute or not ext.attribute):
                return ext.external_id
        return ''

    def get_stocks_with_upc(self):
        stocks = []
        for s in self.available.stocks:
            if (s.variant.isdigit() and s.upc):
                stocks.append(s)
        return stocks

    def get_main_picture(self, id_variant=0):
        """ If id_variant set, return preview img of the variant.
            else return the sale's first product img.
        """
        img_path = None
        if int(id_variant):
            v = self.get_variant(id_variant)
            if v.img:
                img_path = v.img[0]
        elif self.img:
            img_path = self.img[0]
        if img_path:
            return img_path
        else:
            logging.info('No main image for sale: %s, variant: %s',
                         self.id, id_variant)


class CachedSale:
    def __init__(self, sale_id):
        key = SALE % sale_id
        self._xml_sale = get_redis_cli().get(key)
        self._sale = None

    @property
    def sale(self):
        if self._xml_sale is None:
            return

        if self._sale is None:
            self._sale = ActorSale(xml_data=self._xml_sale)

        return self._sale

    def valid(self):
        return self.sale is not None

    def available(self):
        return self.valid() and self.sale.available_now()

    def valid_variant(self, id_variant):
        if not self.valid():
            return False
        id_variant = int(id_variant)
        if not id_variant:
            return True

        try:
            self.sale.get_variant(id_variant)
        except NotExistError:
            return False
        return True

    def valid_type(self, id_type):
        if not self.valid():
            return False
        id_type = int(id_type)
        if not id_type:
            return True

        try:
            self.sale.get_weight_attr(id_type)
        except NotExistError:
            return False
        return True

    def valid_shop(self, id_shop):
        try:
            if int(id_shop):
                self.sale.get_shop(id_shop)
            elif int(id_shop) == 0:
                pass
            elif len(self.sale.shops) > 0:
                raise NotExistError()
        except NotExistError:
            return False
        return True

def get_sale_by_barcode(barcode, shop_id):
    cli = get_redis_cli()
    key = BARCODE % (barcode, shop_id)
    id_sale = cli.hget(key, BARCODE_SALE_ID)
    id_variant = cli.hget(key, BARCODE_VARIANT_ID)
    return id_sale, id_variant
