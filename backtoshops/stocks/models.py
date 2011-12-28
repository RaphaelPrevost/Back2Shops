from django.db import models
from attributes.models import BrandAttribute, CommonAttribute
from sales.models import Sale
from shops.models import Shop

class ProductStock(models.Model):
    sale = models.ForeignKey(Sale, related_name="detailed_stock", on_delete=models.CASCADE)
    brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
    common_attribute = models.ForeignKey(CommonAttribute)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    stock = models.IntegerField()
    rest_stock = models.IntegerField()

    def __unicode__(self):
        return str(self.stock)

