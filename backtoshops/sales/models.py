from django.db import models
from django.utils.translation import ugettext_lazy as _
from accounts.models import Brand
from shops.models import Shop
from sorl.thumbnail import ImageField

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
    shops = models.ManyToManyField(Shop, blank=True, null=True)
    type_stock = models.CharField(max_length=1, choices=STOCK_TYPE_CHOICES, blank=True, null=True)
    total_stock = models.IntegerField(blank=True, null=True)
    total_rest_stock = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=2, choices=GENDERS, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%d - %d' % (self.id, self.total_stock)

class Product(models.Model):
    sale = models.OneToOneField("Sale", blank=True, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey("ProductCategory", related_name="products", blank=False)
    type = models.ForeignKey("ProductType", related_name="products", blank=False)
    brand = models.ForeignKey("ProductBrand", related_name="products")
    currency = models.ForeignKey("ProductCurrency",blank=False)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    normal_price = models.FloatField()
    discount_type = models.CharField(choices=DISCOUNT_TYPE, max_length=10, blank=False)
    discount = models.FloatField()
    discount_price = models.FloatField()
    valid_from = models.DateField()
    valid_to = models.DateField()
    #brand_attributes = models.ManyToManyField("attributes.BrandAttribute", through="attributes.BrandAttributePreview")

    def __unicode__(self):
        return self.name
    
class ProductCurrency(models.Model):
    code = models.CharField(max_length=3)
    description = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.code

    
class ProductPicture(models.Model):
    product = models.ForeignKey("Product", related_name="pictures", null=True, blank=True)
    is_brand_attribute = models.BooleanField(default=False)
    picture = ImageField(upload_to="product_pictures")

    def __unicode__(self):
        return self.picture.url

class ProductCategory(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class ProductType(models.Model):
    name = models.CharField(max_length=50, verbose_name='name')
    category = models.ForeignKey(ProductCategory, verbose_name='category')

    def __unicode__(self):
        return self.name

class ProductBrand(models.Model):
    seller = models.ForeignKey(Brand, related_name="sold_brands")
    name = models.CharField(max_length=50)
    picture = models.ImageField(upload_to="product_brands", default="NULL")

    def __unicode__(self):
        return self.name

