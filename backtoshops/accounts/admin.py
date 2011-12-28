from django.contrib.admin import site
from accounts.models import *

site.register(Brand)
site.register(UserProfile)