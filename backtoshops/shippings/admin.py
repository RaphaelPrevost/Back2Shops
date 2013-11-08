from django.contrib.admin import site
from shippings.models import *

site.register(Carrier)
site.register(Service)
