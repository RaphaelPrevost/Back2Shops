# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from common.cache_invalidation import send_cache_invalidation


class Route(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="route", on_delete=models.DO_NOTHING)

    page_type = models.CharField(verbose_name=_("Page Type"), max_length=100)
    page_role = models.CharField(verbose_name=_("Page Role"), max_length=100)
    title = models.CharField(verbose_name=_("HTML Title"), max_length=100, null=True, blank=True)

    url_format = models.CharField(verbose_name=_("URL"), max_length=100)
    redirects_to = models.ForeignKey("self", verbose_name=_("Redirect To"), null=True, blank=True)
    last_update = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.page_type


class HtmlMeta(models.Model):
    route = models.ForeignKey(Route, related_name='htmlmetas')
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    value = models.CharField(verbose_name=_("value"), max_length=300)


class RouteParam(models.Model):
    route = models.ForeignKey(Route, related_name='routeparams')
    name = models.CharField(verbose_name=_("Name"), blank=True, max_length=100)
    is_required = models.BooleanField(default=0)


@receiver(post_save, sender=Route, dispatch_uid='routes.models.Route')
def on_route_saved(sender, **kwargs):
    method = kwargs.get('created', False) and "POST" or "PUT"
    instance = kwargs.get('instance')
    send_cache_invalidation(method, 'route', instance.mother_brand_id)

@receiver(post_delete, sender=Route, dispatch_uid='routes.models.Route')
def on_route_deleted(sender, **kwargs):
    method = "DELETE"
    instance = kwargs.get('instance')
    send_cache_invalidation(method, 'route', instance.mother_brand_id)
