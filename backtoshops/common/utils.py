from common.constants import USERS_ROLE

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
