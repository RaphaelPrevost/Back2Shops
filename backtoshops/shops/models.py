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


from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from address.models import Address
from common.assets_utils import AssetsStorage
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from shippings.models import Shipping
from sorl.thumbnail import ImageField


class Shop(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="shops")
    gestion_name = models.CharField(verbose_name=_("Internal name"), max_length=100, blank=True, null=True)
    upc = models.CharField(verbose_name=_("Barcode"), max_length=50, blank=True, null=True)
    phone = models.CharField(verbose_name=_("Phone number"), max_length=50, blank=True, null=True)
    name = models.CharField(verbose_name=_("Shop name"), max_length=50)
    catcher = models.CharField(verbose_name=_("Caption"), max_length=250, blank=True, null=True)
    image = ImageField(verbose_name=_("Shop picture"),
                       upload_to="img/shop_images", blank=True, null=True,
                       storage=AssetsStorage())
    description = models.CharField(verbose_name=_("Description"), max_length=500, blank=True, null=True)
    opening_hours = models.CharField(max_length=1000, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.ForeignKey(Address, unique=True)
    owner = models.ForeignKey(User, blank=True, null=True)
    business_reg_num = models.CharField(verbose_name="Business Reg Num", max_length=100, blank=True, null=True)
    tax_reg_num = models.CharField(verbose_name="Tax Reg Num", max_length=100, blank=True, null=True)
    default_currency = models.CharField(verbose_name="Default Currency",
                                        max_length=3, null=True)

    def __unicode__(self):
        return self.name

@receiver(post_save, sender=Shop, dispatch_uid='shops.models.Shop')
def on_shop_saved(sender, **kwargs):
    post_save_handler('shop', sender, **kwargs)

@receiver(post_delete, sender=Shop, dispatch_uid='shops.models.Shop')
def on_shop_deleted(sender, **kwargs):
    post_delete_handler('shop', sender, **kwargs)


class DefaultShipping(models.Model):
    shop = models.ForeignKey(Shop)
    shipping = models.ForeignKey(Shipping)
