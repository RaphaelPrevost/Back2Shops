import logging
from decimal import Decimal
from common.constants import SALE
from common.constants import BARCODE
from common.constants import BARCODE_VARIANT_ID
from common.constants import BARCODE_SALE_ID
from common.error import NotExistError
from common.utils import as_list
from common.utils import order_img_download
from common.redis_utils import get_redis_cli
from models.base_actor import BaseActor


class ActorSaleCategory(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}


class ActorSaleCommonAttr(BaseActor):
    attrs_map = {'id': '@id',
                 'name': '@name'}


class ActorSaleType(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name'}

    @property
    def attributes(self):
        attrs = as_list(self.data.get('attribute', None))
        return [ActorSaleCommonAttr(data=attr) for attr in attrs]


class ActorSaleBrand(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'img': 'img'}


class ActorSalePrice(BaseActor):
    attrs_map = {'currency': '@currency',
                 'text': '#text'}


class ActorSaleDiscount(BaseActor):
    attrs_map = {'type': '@type',
                 'text': '#text'}


class ActorSaleVariantPremium(BaseActor):
    attrs_map = {'type': '@type',
                 'text': '#text'}


class ActorSaleVariant(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'thumb': 'thumb',
                 'img': 'img'}

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
                 'addr': 'addr',
                 'zip': 'zip',
                 'city': 'city',
                 'country': 'country',
                 'upc': 'upc',
                 'hours': 'hours',
                 }

    @property
    def localtion(self):
        return ActorShopLocaltion(data=self.data.get('location'))

class ActorStock(BaseActor):
    attrs_map = {'shop': '@shop',
                 'available': '@available'}

class ActorStocks(BaseActor):
    attrs_map = {'variant': '@variant',
                 'attribute': '@attribute',
                 'upc': 'upc'}

    @property
    def stock(self):
        s = self.data.get('stock', None)
        if s:
            return
        return ActorStock(data=s)


class ActorSaleAvailable(BaseActor):
    attrs_map = {'from': '@from',
                 'to': '@to'}

    @property
    def stocks(self):
        stocks_list = as_list(self.data.get('stocks', None))
        return [ActorStocks(data=stock) for stock in stocks_list]

class ActorSale(BaseActor):
    attrs_map = {'id': '@id',
                 'name': 'name',
                 'desc': 'desc',
                 }

    # attributes set/used in orders
    order_props = None
    shipping_setting = None

    def __repr__(self):
        return "ActorSale:" + '-'.join([self.id, self.name, self.desc])

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
    def price(self):
        return ActorSalePrice(data=self.data['price'])

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
    def available(self):
        return ActorSaleAvailable(data=self.data.get('available'))

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

    def final_price(self, id_variant=0):
        def __diff_price(orig_price, obj):
            if obj is None:
                return 0

            if obj.type == 'ratio':
                return Decimal(orig_price) * Decimal(obj.text) / 100
            else:
                return Decimal(obj.text)

        normal_price = Decimal(self.price.text)
        _discount = __diff_price(normal_price, self.discount)
        price = normal_price - _discount
        if int(id_variant):
            v = self.get_variant(id_variant)
            premium = __diff_price(price, v.premium)
            price = price + premium
        return price

    def whole_name(self, id_variant=0):
        name = self.name
        if int(id_variant):
            v = self.get_variant(id_variant)
            name = '-'.join([name, v.name])
        return name

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
                img_path = v.img
        elif self.img:
            img_path = self.img[0]
        if img_path:
            new_path = order_img_download(img_path)
            return new_path
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

    def valid_shop(self, id_shop):
        try:
            if int(id_shop):
                self.sale.get_shop(id_shop)
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
