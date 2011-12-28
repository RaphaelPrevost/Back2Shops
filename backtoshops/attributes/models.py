from django.db import models
from accounts.models import Brand
from sales.models import Product, ProductPicture, ProductType
from sorl.thumbnail import ImageField

class BrandAttribute(models.Model):
    product = models.ManyToManyField(Product, through="BrandAttributePreview", related_name="brand_attributes")
    mother_brand = models.ForeignKey(Brand, related_name="brand_attributes")
    name = models.CharField(max_length=50, null=True, blank=True)
    texture = ImageField(null=True, upload_to="product_pictures")

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

    def __unicode__(self):
        return self.name