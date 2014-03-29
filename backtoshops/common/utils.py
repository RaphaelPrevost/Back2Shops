from common.constants import USERS_ROLE
from globalsettings import get_setting
from globalsettings.models import SETTING_KEY_CHOICES
from brandsettings import get_ba_settings

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

    value = None
    if shop and shop.owner:
        value = get_ba_settings(shop.owner).get(key)
    if not value:
        value = get_ba_settings(user).get(key)
    if not value and key in dict(SETTING_KEY_CHOICES):
        value = get_setting(key)
    return value

