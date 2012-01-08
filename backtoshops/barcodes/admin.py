from django.contrib.admin import site
from barcodes.models import *

site.register(Barcode)
