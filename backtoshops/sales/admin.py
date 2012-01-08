from django.contrib.admin import site
from sales.models import *

site.register(Sale)
site.register(Product)
site.register(ProductBrand)
site.register(ProductCategory)
site.register(ProductPicture)
site.register(ProductType)
site.register(ProductCurrency)
