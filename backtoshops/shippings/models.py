from django.db import models
from django.utils.translation import ugettext_lazy as _
from accounts.models import Brand
from globalsettings import get_setting

SC_FREE_SHIPPING = 1
SC_FLAT_RATE = 2
SC_CARRIER_SHIPPING_RATE = 3
SC_CUSTOM_SHIPPING_RATE = 4
SC_INVOICE = 5
SHIPPING_CALCULATION = (
    (SC_FREE_SHIPPING, _('Free shipping')),
    (SC_FLAT_RATE, _('Flat rate')),
    (SC_CARRIER_SHIPPING_RATE, _('Carrier Shipping Rate')),
    (SC_CUSTOM_SHIPPING_RATE, _('Custom Shipping Rate')),
    (SC_INVOICE, _('Invoice')),
)


STOY_WEIGHT = 'W'
STOY_PRICE = 'P'
SHIPPING_TOTAL_ORDER_TYPE = (
    (STOY_WEIGHT, _('Weight')),
    (STOY_PRICE, _('Price')),
)


class Carrier(models.Model):
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=50)
    carrier = models.ForeignKey(Carrier, related_name='services')

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

    def __unicode__(self):

        t_type = dict(SHIPPING_TOTAL_ORDER_TYPE
                    ).get(self.total_order_type).lower()
        #TODO: the weight unit shoule be implemented in #63.
        t_unit = self.total_order_type == STOY_PRICE and get_setting('default_currency') or 'kg'
        return ('%s: %s, %s between %s %s and %s %s'
                % (self.shipping_rate, self.shipment_type, t_type,
                   self.total_order_lower, t_unit,
                   self.total_order_upper, t_unit))


class ServiceInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    service = models.ForeignKey(Service)


class CustomShippingRateInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    custom_shipping_rate = models.ForeignKey(CustomShippingRate)


class FlatRateInShipping(models.Model):
    shipping = models.ForeignKey(Shipping)
    flat_rate = models.FloatField(blank=True, null=True)
