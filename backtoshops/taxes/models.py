from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler
from countries.models import Country
from sales.models import ProductCategory


class Rate(models.Model):
    name = models.CharField(max_length=50)
    region = models.ForeignKey(Country, related_name='region')
    province = models.CharField(max_length=50, null=True, blank=True)
    applies_to = models.ForeignKey(ProductCategory, null=True, blank=True)
    shipping_to_region = models.ForeignKey(Country, null=True, blank=True,
                                           related_name='shipping_to_region')
    shipping_to_province = models.CharField(max_length=50, null=True, blank=True)
    rate = models.FloatField()
    apply_after = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField()
    display_on_front = models.NullBooleanField(null=True, blank=True)
    taxable = models.NullBooleanField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s - %s%%' % (self.name, self.region, self.rate)

@receiver(post_save, sender=Rate, dispatch_uid='taxes.models.Rate')
def on_rate_saved(sender, **kwargs):
    post_save_handler('tax', sender, **kwargs)

@receiver(post_delete, sender=Rate, dispatch_uid='taxes.models.Rate')
def on_rate_deleted(sender, **kwargs):
    post_delete_handler('tax', sender, **kwargs)

