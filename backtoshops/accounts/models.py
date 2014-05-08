from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from address.models import Address
from common.assets_utils import AssetsStorage
from common.constants import USERS_ROLE


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    work_for = models.ForeignKey("Brand", related_name="employee")
    shops = models.ManyToManyField('shops.Shop', verbose_name=_('shops'), null=True, blank=True)
    language = models.CharField(max_length=2, verbose_name=_('language'), choices=settings.LANGUAGES)
    role = models.IntegerField()
    allow_internet_operate = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Brand(models.Model):
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="img/brand_logos",
                                       storage=AssetsStorage())
    address = models.ForeignKey(Address, unique=True)
    business_reg_num = models.CharField(verbose_name="Business Registration Number", max_length=100)
    tax_reg_num = models.CharField(verbose_name="Tax Registration Number", max_length=100)

    def __str__(self):
        return self.name

