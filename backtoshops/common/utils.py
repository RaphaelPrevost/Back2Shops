import logging
import time

from common.constants import USERS_ROLE
from globalsettings import get_setting
from globalsettings.models import SETTING_KEY_CHOICES
from brandsettings import get_ba_settings
from brandsettings.models import SETTING_KEY_CHOICES as BRAND_SETTING_KEY_CHOICES

GRAM_OZ_CONVERSION = 0.0352739619
OZ_GRAM_CONVERSION = 28.3495231

def format_epoch_time(seconds, format='%d/%m/%Y %H:%M'):
    return time.strftime(format, time.gmtime(seconds))

def gram_to_oz(weight):
    return weight * GRAM_OZ_CONVERSION

def oz_to_gram(weight):
    return weight * OZ_GRAM_CONVERSION

def is_shop_manager(profile_pk):
    from accounts.models import UserProfile
    profile = UserProfile.objects.get(pk=profile_pk)
    return (profile.role == USERS_ROLE.MANAGER and
            len(profile.shops.all()) > 0 )

def is_shop_manager_upper(profile_pk):
    from accounts.models import UserProfile
    profile = UserProfile.objects.get(pk=profile_pk)
    return ((profile.role < USERS_ROLE.MANAGER) or
            (profile.role == USERS_ROLE.MANAGER and
             len(profile.shops.all()) > 0))

def get_currency(user, shop=None):
    default_currency = get_setting('default_currency')
    if user.is_superuser:
        return default_currency

    value = None
    if shop:
        value = shop.default_currency
    if not value:
        value = get_ba_settings(user).get('default_currency')
    return value or default_currency

def get_brand_currency(user):
    default_currency = get_setting('default_currency')
    value = get_ba_settings(user).get('default_currency')
    return value or default_currency

def get_default_setting(key, user, shop=None):
    if user.is_superuser: return
    if key not in dict(BRAND_SETTING_KEY_CHOICES): return

    value = None
    if shop and shop.owner:
        value = get_ba_settings(shop.owner).get(key)
    if not value:
        value = get_ba_settings(user).get(key)
    if not value and key in dict(SETTING_KEY_CHOICES):
        value = get_setting(key)
    return value

def get_merchant_address(user_profile, id_shop=None):
    from accounts.models import Brand
    from shops.models import Shop

    if id_shop is not None and int(id_shop) == 0:
        id_shop = None

    id_brand = user_profile.work_for_id
    if user_profile.role == USERS_ROLE.ADMIN:
        if id_shop is not None:
            shop = Shop.objects.get(pk=id_shop)
            if shop.mother_brand_id == id_brand:
                return shop.address
            else:
                raise Exception("addr_auth_err: merchant: %s, "
                                "shop: %s" % (user_profile.id, id_shop))
        else:
            return Brand.objects.get(pk=id_brand).address
    elif user_profile.role == USERS_ROLE.MANAGER:
        if id_shop is not None and int(id_shop) != 0:
            manage_shops = user_profile.shops.all()

            if int(id_shop) in [s.id for s in manage_shops]:
                return Shop.objects.get(pk=id_shop).address
            else:
                raise Exception("addr_auth_err: merchant: %s, "
                                "shop: %s" % (user_profile.id, id_shop))
        else:
            if user_profile.allow_internet_operate:
                return Brand.objects.get(pk=id_brand).address
            else:
                raise Exception("addr_auth_err: merchant: %s, "
                                "shop: %s" % (user_profile.id, id_shop))
    else:
        if id_shop is not None and int(id_shop) != 0:
            manage_shops = user_profile.shops.all()

            if int(id_shop) in [s.id for s in manage_shops]:
                return Shop.objects.get(pk=id_shop).address
            else:
                raise Exception("addr_auth_err: merchant: %s, "
                                "shop: %s" % (user_profile.id, id_shop))
        else:
            raise Exception("addr_auth_err: merchant: %s, "
                            "shop: %s" % (user_profile.id, id_shop))


def get_valid_sort_fields(order_by1, order_by2, default_sort_field=None):
    sort_fields = []
    for field in [order_by1, order_by2]:
        if field and field not in sort_fields:
            sort_fields.append(field)

    if not sort_fields and default_sort_field:
        sort_fields = [default_sort_field]
    return sort_fields

class Sorter(object):
    def __init__(self, object_list):
        self.object_list = object_list

    def sort(self, sort_fields, get_sort_field_func=None):
        # sort_fields is a list of field in order of priority
        # e.g. ['creation', '-shop_id', 'product__valid_to']
        # '__' is the split for child attribute.
        # e.g. 'product__valid_to', will first get attribute with 'product'
        #      then get attribute 'valid_to'.

        sort_fields = [f for f in sort_fields if f]
        if not sort_fields: return

        if get_sort_field_func is None:
            def __sort_field_func(item, field):
                attrs = field.split('__')
                for attr in attrs:
                    item = getattr(item, attr, None)
                return item
            get_sort_field_func = __sort_field_func

        self.object_list.sort(lambda x, y: self._cmp(x, y, sort_fields,
                                                     get_sort_field_func))

    def _cmp(self, item1, item2, sort_fields, func):
        result = 0
        for field in sort_fields:
            if field.startswith('-'):
                field = field[1:]
                direction = -1
            else:
                direction = 1

            if result != 0:
                break
            try:
                result = cmp(func(item1, field), func(item2, field))
                result *= direction
            except Exception, e:
                logging.error("Got Exception when sorting,"
                              "sort_field %s, item1: %s, item2: %s, error: %s",
                              field, item1, item2, e, exc_info=True)
                break
        return result



OZ_GRAM_CONVERSION = 28.3495231
LB_GRAM_CONVERSION = 453.59237
GRAM_KILOGRAM_CONVERSION = 0.001

def oz_to_gram(weight):
    return weight * OZ_GRAM_CONVERSION

def gram_to_kilogram(weight):
    return weight * GRAM_KILOGRAM_CONVERSION

def lb_to_gram(weight):
    return weight * LB_GRAM_CONVERSION

def weight_convert(from_unit, weight):
    weight = float(weight)
    if from_unit == 'kg':
        return weight
    elif from_unit == 'g':
        return gram_to_kilogram(weight)
    elif from_unit == 'oz':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)
    elif from_unit == 'lb':
        weight_in_gram = oz_to_gram(weight)
        return gram_to_kilogram(weight_in_gram)
