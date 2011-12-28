from django.contrib.admin import site
from attributes.models import *

site.register(BrandAttribute)
site.register(CommonAttribute)
