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

from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from countries.models import Country
from sales.models import ProductCategory


class Rate(models.Model):
    name = models.CharField(max_length=50)
    region = models.ForeignKey(Country, related_name='region')
    province = models.CharField(max_length=50, null=True, blank=True)
    applies_to = models.ForeignKey(ProductCategory, null=True, blank=True)
    shipping_to_region = models.ForeignKey(Country, null=True, blank=True,
                                           related_name='shipping_to_region')
    shipping_to_province = models.CharField(max_length=50, null=True, blank=True)
    rate = models.FloatField()
    apply_after = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField()
    display_on_front = models.NullBooleanField(null=True, blank=True)
    taxable = models.NullBooleanField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s - %s%%' % (self.name, self.region, self.rate)

@receiver(post_save, sender=Rate, dispatch_uid='taxes.models.Rate')
def on_rate_saved(sender, **kwargs):
    post_save_handler('tax', sender, **kwargs)

@receiver(post_delete, sender=Rate, dispatch_uid='taxes.models.Rate')
def on_rate_deleted(sender, **kwargs):
    post_delete_handler('tax', sender, **kwargs)

