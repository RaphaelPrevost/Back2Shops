from django.db import models
from attributes.models import BrandAttribute, CommonAttribute
from sales.models import Sale

class Barcode(models.Model):
	upc = models.CharField(max_length=50)
	sale = models.ForeignKey(Sale, related_name="barcodes", on_delete=models.CASCADE)
	brand_attribute = models.ForeignKey(BrandAttribute, null=True, blank=True)
	common_attribute = models.ForeignKey(CommonAttribute)