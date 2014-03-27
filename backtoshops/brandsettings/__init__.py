from common.constants import USERS_ROLE
from models import BrandSettings


def get_ba_settings(user):
    if user.is_superuser: return
    u_profile = user.get_profile()

    if u_profile.role == USERS_ROLE.ADMIN:
        # brand admin settings
        settings = _query_by_user(user)
        settings = _convert_queryset_to_dict(settings)
    elif u_profile.role == USERS_ROLE.MANAGER:
        # manager's settings override brand admin settings
        settings = _query_by_user(user, user_role=USERS_ROLE.ADMIN)
        settings = _convert_queryset_to_dict(settings)
        m_settings = _query_by_user(user)
        m_settings = _convert_queryset_to_dict(m_settings)
        settings.update(m_settings)
    else:
        # brand admin settings
        settings = _query_by_user(user, user_role=USERS_ROLE.ADMIN)
        settings = _convert_queryset_to_dict(settings)
    return settings

def save_ba_settings(user, data):
    if user.is_superuser: return
    u_profile = user.get_profile()
    if u_profile.role > USERS_ROLE.MANAGER: return

    settings = _query_by_user(user)
    # update or delete
    if settings:
        for s in settings:
            if s.key in data:
                s.value = data.pop(s.key)
                s.save() if s.value else s.delete()

    # insert
    brand = u_profile.work_for
    for k, v in data.iteritems():
        if not v: continue

        if u_profile.role == USERS_ROLE.ADMIN:
            shopowner = None
        elif u_profile.role == USERS_ROLE.MANAGER:
            shopowner = user
        else:
            continue
        s = BrandSettings(key=k, value=v, brand=brand,
                          shopowner=shopowner)
        s.save()

def _query_by_user(user, user_role=None):
    if user.is_superuser: return

    u_profile = user.get_profile()
    if user_role:
        # get settings in own or upper privilege level
        assert user_role <= u_profile.role
    else:
        # get settings in own privilege level
        user_role = u_profile.role

    shopowner = None
    if u_profile.role == USERS_ROLE.MANAGER \
            and user_role == USERS_ROLE.MANAGER:
        shopowner = user

    try:
        settings = BrandSettings.objects.filter(
                            brand=u_profile.work_for, shopowner=shopowner)
    except BrandSettings.DoesNotExist:
        settings = None
    return settings

def _convert_queryset_to_dict(qs):
    return dict(qs.values_list('key', 'value')) if qs else {}

