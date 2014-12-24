# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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

