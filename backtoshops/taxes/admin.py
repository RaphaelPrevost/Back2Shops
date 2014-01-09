from django.contrib.admin import site
from taxes.models import Rate

site.register(Rate)
