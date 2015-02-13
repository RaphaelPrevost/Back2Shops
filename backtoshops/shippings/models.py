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
from django.utils.translation import ugettext_lazy as _
from accounts.models import Brand

from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SC_METHODS
from B2SProtocol.settings import SHIPPING_CURRENCY
from B2SProtocol.settings import SHIPPING_WEIGHT_UNIT

SC_FREE_SHIPPING = SC_METHODS.FREE_SHIPPING
SC_FLAT_RATE = SC_METHODS.FLAT_RATE
SC_CARRIER_SHIPPING_RATE = SC_METHODS.CARRIER_SHIPPING_RATE
SC_CUSTOM_SHIPPING_RATE = SC_METHODS.CUSTOM_SHIPPING_RATE
SC_INVOICE = SC_METHODS.INVOICE

SHIPPING_CALCULATION = (
    (SC_FREE_SHIPPING, _('Free shipping')),
    (SC_FLAT_RATE, _('Flat rate')),
    (SC_CARRIER_SHIPPING_RATE, _('Carrier Shipping Rate')),
    (SC_CUSTOM_SHIPPING_RATE, _('Custom Shipping Rate')),
    (SC_INVOICE, _('Invoice')),
)


STOY_WEIGHT = 'W'
STOY_PRICE = 'P'
STOY_COUNTRY = 'C'
STOY_REGION = 'R'
SHIPPING_TOTAL_ORDER_TYPE = (
    (STOY_WEIGHT, _('Weight')),
    (STOY_PRICE, _('Price')),
    (STOY_COUNTRY, _('Country: France')),
    (STOY_REGION, _('Region: Europe')),
)


class Carrier(models.Model):
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=50, blank=True)
    desc = models.TextField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=50)
    carrier = models.ForeignKey(Carrier, related_name='services')
    desc = models.TextField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return self.carrier.name + ' - ' + self.name


class Shipping(models.Model):
   #sale = models.OneToOneField("Sale", blank=True, null=True)
    handling_fee = models.FloatField(null=True)
    allow_group_shipment = models.BooleanField()
    allow_pickup = models.BooleanField()
    pickup_voids_handling_fee = models.BooleanField()
    shipping_calculation = models.SmallIntegerField(
        choices=SHIPPING_CALCULATION)


class CustomShippingRate(models.Model):
    seller = models.ForeignKey(Brand)
    shipment_type = models.CharField(max_length=50)
    total_order_type = models.CharField(max_length=2,
                                        verbose_name='Total order',
                                        choices=SHIPPING_TOTAL_ORDER_TYPE)
    total_order_upper = models.FloatField()
    total_order_lower = models.FloatField()
    shipping_rate = models.FloatField(verbose_name='Set shipping rate to')
    desc = models.TextField(max_length=500,
                            verbose_name='Description',
                            null=True, blank=True)

    def __unicode__(self):

        t_type = dict(SHIPPING_TOTAL_ORDER_TYPE
                    ).get(self.total_order_type).lower()
        if self.total_order_type in (STOY_PRICE, STOY_WEIGHT):
            t_unit = (self.total_order_type == STOY_PRICE and
                      SHIPPING_CURRENCY or
                      SHIPPING_WEIGHT_UNIT)
            return ('%s: %s, %s between %s %s and %s %s'
                    % (self.shipping_rate, self.shipment_type, t_type,
                       self.total_order_lower, t_unit,
                       self.total_order_upper, t_unit))
        else:
            return ('%s: %s, %s'
                    % (self.shipping_rate, self.shipment_type, t_type))

class ServiceInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    service = models.ForeignKey(Service)


class CustomShippingRateInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    custom_shipping_rate = models.ForeignKey(CustomShippingRate)


class FlatRateInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    flat_rate = models.FloatField(blank=True, null=True)
