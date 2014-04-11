from common.constants import SHOP_WITH_BARCODE
from common.constants import SHOP
from common.redis_utils import get_redis_cli
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
