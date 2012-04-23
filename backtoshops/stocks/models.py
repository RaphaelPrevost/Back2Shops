from django.db import models
from attributes.models import BrandAttribute, CommonAttribute
from sales.models import Sale
from shops.models import Shop

class ProductStock(models.Model):
    sale = models.ForeignKey(Sale, related_name="detailed_stock", on_delete=models.CASCADE)
    brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
    common_attribute = models.ForeignKey(CommonAttribute)
    shop = models.ForeignKey(Shop, null=True, blank=True)
    stock = models.IntegerField(default=0)
    rest_stock = models.IntegerField(default=0)

    def __unicode__(self):
        return '%d:%d:%s'%(self.stock,self.rest_stock,self.sale)

