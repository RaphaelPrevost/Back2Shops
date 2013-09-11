import binascii
import os
import random

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.encoding import smart_str
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


def get_hexdigest(algorithm, iteration_count, salt, raw_password):
    raw_password, salt = smart_str(raw_password), smart_str(salt)

    if algorithm == 1:
        import whirlpool
        result = whirlpool.new(salt + raw_password).hexdigest()
    else:
        raise ValueError("Got unknown password algorithm type in password.")

    iteration_count = iteration_count - 1
    if iteration_count > 0:
        return get_hexdigest(algorithm, iteration_count, result, raw_password)
    else:
        return result

class EndUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    salt = models.CharField(max_length=128)
    hash_iteration_count = models.IntegerField()
    hash_algorithm = models.IntegerField()

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        if raw_password is None:
            self.password = None
        else:
            hash_algorithm = settings.DEFAULT_HASH_ALGORITHM
            hash_iteration_count = random.randint(settings.HASH_MIN_ITERATIONS,
                                                  settings.HASH_MAX_ITERATIONS)
            salt = binascii.b2a_hex(os.urandom(64))
            self.password = get_hexdigest(hash_algorithm, hash_iteration_count,
                                          salt, raw_password)
            self.salt = salt
            self.hash_algorithm = hash_algorithm
            self.hash_iteration_count = hash_iteration_count

