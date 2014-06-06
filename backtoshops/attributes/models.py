from django.db import models
from django.utils.translation import ugettext_lazy as _
from sorl.thumbnail import ImageField

from accounts.models import Brand
from common.assets_utils import AssetsStorage
from sales.models import DISCOUNT_TYPE
from sales.models import Product
from sales.models import ProductPicture
from sales.models import ProductType


class BrandAttribute(models.Model):
    product = models.ManyToManyField(Product,
                                     through="BrandAttributePreview",
                                     related_name="brand_attributes")
    mother_brand = models.ForeignKey(Brand,
                                     related_name="brand_attributes")
    name = models.CharField(max_length=50, null=True, blank=True)
    texture = ImageField(upload_to="img/product_pictures",
                         storage=AssetsStorage(), null=True)
    premium_type = models.CharField(choices=DISCOUNT_TYPE,
                                    verbose_name=_('type of premium price'),
                                    max_length=10, blank=True, null=True)
    premium_amount = models.FloatField(verbose_name=_('amount of premium'),
                                       null=True)

    def __unicode__(self):
        return self.name

class BrandAttributePreview(models.Model):
    product = models.ForeignKey(Product)
    brand_attribute = models.ForeignKey(BrandAttribute)
    preview = models.ForeignKey(ProductPicture, null=True)

#class BrandAttributePicture(models.Model):
#    attribute = models.ForeignKey("BrandAttribute", related_name="pictures")
#    file = models.ImageField(upload_to="attribute_pictures")

class CommonAttribute(models.Model):
    for_type = models.ForeignKey(ProductType, related_name="common_attributes")
    name = models.CharField(max_length=50)
    valid = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    def delete(self, using=None):
        if self.barcode_set.all() or self.productstock_set.all():
            self.valid = False
            self.save()
        else:
            super(CommonAttribute, self).delete(using)
