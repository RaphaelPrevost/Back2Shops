from pymongo import Connection, GEO2D

from shops.models import Shop


def build_index():
    db = Connection().backtoshops
    db.shops.create_index([('loc', GEO2D)])
    
    for shop in Shop.objects.all():
        db.shops.insert({
            'shop_id': shop.id,
            'loc': (shop.longitude, shop.latitude),
        })
