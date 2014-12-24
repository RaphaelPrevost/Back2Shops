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
