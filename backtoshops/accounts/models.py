from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    work_for = models.ForeignKey("Brand", related_name="employee")
    shops = models.ManyToManyField('shops.Shop', verbose_name=_('shops'), null=True, blank=True)
    language = models.CharField(max_length=2, verbose_name=_('language'), choices=settings.LANGUAGES)

    def __str__(self):
        return self.user.username

class Brand(models.Model):
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to="brand_logos")

    def __str__(self):
        return self.name

