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
from django.contrib.auth.models import User

from accounts.models import Brand
from shops.models import Shop

SETTING_KEY_CHOICES = (
                       ('default_currency', 'default currency'),
                       ('default_shipment_period', 'default shipment period'),
                       ('default_payment_period', 'default payment period'),
                       ('starting_invoice_number', 'starting invoice number'),
                       ('use_after_tax_price', 'use after tax price'),
                       ('order_require_confirmation', 'order require confirmation'),
                       ('unique_items', 'unique items'),
                       )

# Create your models here.
class BrandSettings(models.Model):
    key = models.CharField(max_length=200, choices=SETTING_KEY_CHOICES)
    value = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand)
    shopowner = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        unique_together = (("key", "value", "brand", "shopowner"),)

    def __unicode__(self):
        return self.key


class InvoiceNumber(models.Model):
    shop = models.ForeignKey(Shop, blank=True, null=True)
    brand = models.ForeignKey(Brand)
    invoice_number = models.IntegerField()

    class Meta:
        unique_together = ('shop', 'brand')
