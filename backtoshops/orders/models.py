# coding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from sorl.thumbnail import ImageField
from accounts.models import Brand
from sales.models import Sale
from shippings.models import Carrier, Service
from shops.models import Shop


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
    shipment = models.IntegerField(verbose_name='Order',
                                   blank=False,
                                   null=False)

    def __unicode__(self):
        return str(self.order)


class Order(models.Model):
    id_user = models.IntegerField()
    confirmation_time = models.DateTimeField()

    class Meta:
        db_table = 'orders'


class OrderItems(models.Model):
    id_sale = models.ForeignKey(Sale)
    id_shop = models.ForeignKey(Shop)
    id_variant = models.ForeignKey(Brand)
    price = models.FloatField()
    name = models.CharField(max_length=150)
    picture = ImageField(upload_to='order_item')
    description = models.TextField(max_length=128)
    copy_time = models.DateTimeField()
    barcode = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class OrderDetails(models.Model):
    id_order = models.ForeignKey(Order)
    id_item = models.ForeignKey(OrderItems)
    quantity = models.IntegerField()

