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


from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from sales.models import ProductType
from sales.models import Sale
from shops.models import Shop

class Group(models.Model):
    name = models.CharField(verbose_name=_("Group Name"), max_length=50)
    types = models.ManyToManyField(ProductType, blank=True, null=True, through="TypesInGroup")
    sales = models.ManyToManyField(Sale, blank=True, null=True, through="SalesInGroup")
    brand = models.ForeignKey(Brand)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

class TypesInGroup(models.Model):
    group = models.ForeignKey(Group)
    type = models.ForeignKey(ProductType)

class SalesInGroup(models.Model):
    group = models.ForeignKey(Group)
    sale = models.ForeignKey(Sale)


@receiver(post_delete, sender=Group, dispatch_uid='promotion.models.Group')
def on_group_deleted(sender, **kwargs):
    post_delete_handler('group', sender, **kwargs)

@receiver(post_save, sender=Group, dispatch_uid='promotion.models.Group')
def on_group_saved(sender, **kwargs):
    post_save_handler('group', sender, **kwargs)
