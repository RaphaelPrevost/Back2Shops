# coding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from shippings.models import Carrier, Service


class Shipping(models.Model):
    addr_orig = models.CharField(verbose_name=_("Origin Address"), max_length=128)
    addr_dest = models.CharField(verbose_name=_("Destination Address"), max_length=128)
    weight = models.FloatField(blank=True, null=True)
    carrier = models.ForeignKey(Carrier, verbose_name=_('Carrier'), blank=True, null=True)
    service = models.ForeignKey(Service, verbose_name=_('Service'), blank=True, null=True)
    handling_fee = models.DecimalField(verbose_name=_('Handling Fees'),
                                       max_digits=10,
                                       decimal_places=2,
                                       blank=True,
                                       null=True)
    ship_and_handling_fee = models.DecimalField(
                                       verbose_name=_('Shipping & Handling Fee'),
                                       max_digits=10,
                                       decimal_places=2,
                                       blank=True,
                                       null=True)
    total_fee = models.DecimalField(verbose_name=_('Fee'),
                                    max_digits=10,
                                    decimal_places=2,
                                    blank=True,
                                    null=True)
    order = models.IntegerField(verbose_name='Order')

    def __unicode__(self):
        return str(self.order)
