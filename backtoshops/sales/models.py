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
from sorl.thumbnail import ImageField
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Brand
from common.assets_utils import AssetsStorage
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from shippings.models import Shipping
from shops.models import Shop

GENDERS = (
    ('U', _('Unapplicable')),
    ('M', _('Male')),
    ('F', _('Female'))
)

STOCK_TYPE_DETAILED = "L"
STOCK_TYPE_GLOBAL = "N"
STOCK_TYPE_CHOICES = (
    (STOCK_TYPE_DETAILED, _('Initial stock allocation')),
    (STOCK_TYPE_GLOBAL, _('Initial stock quantities'))
)

DISCOUNT_TYPE = (
    ('percentage', _('Percentage')),
    ('amount', _('Amount'))
)


class Sale(models.Model):
    direct_sale = models.BooleanField(default=False)
    mother_brand = models.ForeignKey(Brand, related_name="sales", on_delete=models.DO_NOTHING)
    shops = models.ManyToManyField(Shop, blank=True, null=True, through='ShopsInSale')
    type_stock = models.CharField(max_length=1, choices=STOCK_TYPE_CHOICES, blank=True, null=True)
    total_stock = models.IntegerField(blank=True, null=True)
    total_rest_stock = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=2, choices=GENDERS, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return unicode('%s - %s' % (self.id, self.total_stock))


class ShopsInSale(models.Model):
    sale = models.ForeignKey(Sale)
    shop = models.ForeignKey(Shop)
    is_freezed = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s-%s-%s' %(self.sale, self.shop, self.is_freezed)

class Product(models.Model):
    sale = models.OneToOneField("Sale", blank=True, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey("ProductCategory", related_name="products", blank=False)
    type = models.ForeignKey("ProductType", related_name="products", blank=False)
    brand = models.ForeignKey("ProductBrand", related_name="products")
    currency = models.ForeignKey("ProductCurrency",blank=False)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    weight_unit = models.ForeignKey("WeightUnit",blank=False,default='kg')
    standard_weight = models.FloatField(null=True, blank=True)
    normal_price = models.FloatField(null=True)
    #brand_attributes = models.ManyToManyField("attributes.BrandAttribute", through="attributes.BrandAttributePreview")
    short_description = models.CharField(max_length=240, blank=True, null=True)
    available_from = models.DateField(null=True)
    available_to = models.DateField(null=True)

    def __unicode__(self):
        return self.name

    @property
    def discount_type(self):
        return 'percentage'

    @property
    def discount(self):
        if hasattr(self, '_discount'):
            return self._discount

        from datetime import datetime
        from B2SUtils.common import parse_ts
        from common.coupons import get_item_specific_discount_coupon
        coupon = get_item_specific_discount_coupon(self.sale.mother_brand.id,
                                                   id_sale=self.sale.id)
        if coupon and (not coupon.valid.from_
                or parse_ts(coupon.valid.from_) <= datetime.now()) \
            and (not coupon.valid.to_
                or parse_ts(coupon.valid.to_) > datetime.now()):
            self._discount = float(coupon.reward.rebate.ratio)
        else:
            self._discount = 0

        return self._discount


class ProductCurrency(models.Model):
    code = models.CharField(max_length=3)
    description = models.CharField(max_length=200)

    def __unicode__(self):
        return self.code


class ProductPicture(models.Model):
    product = models.ForeignKey("Product", related_name="pictures", null=True, blank=True)
    is_brand_attribute = models.BooleanField(default=False)
    picture = ImageField(upload_to="img/product_pictures",
                         storage=AssetsStorage())
    sort_order = models.SmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.picture.url

class ProductCategory(models.Model):
    name = models.CharField(max_length=50)
    valid = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to='img/category_images',
                                  null=True, blank=True,
                                  storage=AssetsStorage())
    picture = models.ImageField(upload_to='img/category_images',
                                null=True, blank=True,
                                storage=AssetsStorage())
    brand = models.ForeignKey(Brand, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def delete(self, using=None):
        if self.products.all():
            self.valid = False
            self.save()
        else:
            # Can't use 'super', why?
            from django.db import models
            models.Model.delete(self, using)


class ProductType(models.Model):
    name = models.CharField(max_length=50, verbose_name='name')
    valid = models.BooleanField(default=True)
    sort_order = models.SmallIntegerField(null=True, blank=True)
    brand = models.ForeignKey(Brand, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def delete(self, using=None):
        if self.products.all():
            for ca in self.common_attributes.all():
                ca.delete()
            self.valid = False
            self.save()
        else:
            # Can't use 'super', why?
            from django.db import models
            models.Model.delete(self, using)

class ProductTypeVarAttr(models.Model):
    from attributes.models import VariableAttribute
    sale = models.ForeignKey(Sale, related_name="type_varattrs", on_delete=models.CASCADE)
    attr = models.ForeignKey(VariableAttribute)
    value = models.CharField(max_length=50)

class CategoryTypeMap(models.Model):
    category = models.ForeignKey(ProductCategory, verbose_name='category')
    type = models.ForeignKey(ProductType, verbose_name='type')


class ProductBrand(models.Model):
    seller = models.ForeignKey(Brand, related_name="sold_brands")
    name = models.CharField(max_length=50)
    picture = models.ImageField(upload_to="img/product_brands", default="NULL",
                                storage=AssetsStorage())

    def __unicode__(self):
        return self.name


class TypeAttributePrice(models.Model):
    from attributes.models import CommonAttribute
    sale = models.ForeignKey(Sale)
    type_attribute = models.ForeignKey(CommonAttribute)
    type_attribute_price = models.FloatField()


class TypeAttributeWeight(models.Model):
    from attributes.models import CommonAttribute
    sale = models.ForeignKey(Sale)
    type_attribute = models.ForeignKey(CommonAttribute)
    type_attribute_weight = models.FloatField()


@receiver(post_delete, sender=Sale, dispatch_uid='sales.models.Sale')
def on_sale_deleted(sender, **kwargs):
    post_delete_handler('sale', sender, **kwargs)
    from promotion.utils import drop_sale_promotion_handler
    drop_sale_promotion_handler(kwargs.get('instance'))

@receiver(post_save, sender=ProductType, dispatch_uid='sales.models.ProductType')
def on_type_saved(sender, **kwargs):
    post_save_handler('type', sender, **kwargs)

@receiver(post_save, sender=ProductCategory, dispatch_uid='sales.models.ProductCategory')
def on_category_saved(sender, **kwargs):
    post_save_handler('cate', sender, **kwargs)

class ShippingInSale(models.Model):
    sale = models.OneToOneField(Sale)
    shipping = models.OneToOneField(Shipping)

ITEM_WEIGHT_CHOICES = (('kg', 'Kilogram'),
                       ('g', 'Gram'),
                       ('lb', 'Pound'),
                       ('oz', 'Ounce'))
class WeightUnit(models.Model):
    key = models.CharField(max_length=2,primary_key=True,choices=ITEM_WEIGHT_CHOICES)
    description = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        return self.key


class ExternalRef(models.Model):
    from attributes.models import BrandAttribute, CommonAttribute
    external_id = models.CharField(max_length=50)
    sale = models.ForeignKey(Sale, related_name="externalrefs", on_delete=models.CASCADE)
    brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
    common_attribute = models.ForeignKey(CommonAttribute, null=True, blank=True)

class OrderConfirmSetting(models.Model):
    from attributes.models import BrandAttribute, CommonAttribute
    require_confirm = models.BooleanField(default=False)
    sale = models.ForeignKey(Sale, related_name="orderconfirmsettings", on_delete=models.CASCADE)
    brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
    common_attribute = models.ForeignKey(CommonAttribute, null=True, blank=True)

