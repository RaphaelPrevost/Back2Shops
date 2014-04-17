import logging

from common.constants import USERS_ROLE
from globalsettings import get_setting
from globalsettings.models import SETTING_KEY_CHOICES
from brandsettings import get_ba_settings
from brandsettings.models import SETTING_KEY_CHOICES as BRAND_SETTING_KEY_CHOICES

GRAM_OZ_CONVERSION = 0.0352739619
OZ_GRAM_CONVERSION = 28.3495231

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

