import ujson
from common.constants import BARCODE_SHOP
from common.constants import SHOP
from common.redis_utils import get_redis_cli
from models.base_actor import BaseActor

def get_shop_id(upc_shop):
    cli = get_redis_cli()
    barcode_key = BARCODE_SHOP % upc_shop
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

class Location(BaseActor):
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
                 'hours': 'hours'
                 }
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
