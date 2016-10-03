# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


from django import template
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from common.constants import USERS_ROLE

register = template.Library()

def _wrap(tip):
    return '<span class="helptext">{}</span>'.format(tip)

@register.simple_tag
@register.filter
def show_sale_uncategorized_tip(category):
    return len(category.field.queryset) == 0

@register.simple_tag
@register.filter
def sale_uncategorized_tip(user):
    if user.is_superuser or user.get_profile().role == USERS_ROLE.OPERATOR:
        return ''

    user_profile = user.get_profile()
    if user_profile.role == USERS_ROLE.ADMIN:
        tip = (
            'Sales are currently uncategorized. '
            'Categories can be created <a href="{}">in your Settings Panel</a>.'
            .format(reverse('list_categories'))
        )
    elif user_profile.role == USERS_ROLE.MANAGER:
        user_cls = get_user_model()
        brand_admin = None
        for profile in UserProfile.objects.filter(
                work_for=user_profile.work_for, role=USERS_ROLE.ADMIN):
            if profile.user.is_active:
                brand_admin = profile.user
                break
        if brand_admin:
            admin_contact = '{} ({})'.format(
                brand_admin.get_full_name() or 'your administrator',
                brand_admin.email)
        else:
            admin_contact = 'your administrator'
        tip = (
            'Sales are currently uncategorized. '
            'Categories can be created by {}.'.format(admin_contact)
        )

    return _wrap(tip)
