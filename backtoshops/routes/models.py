from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from accounts.models import Brand
from common.cache_invalidation import post_delete_handler
from common.cache_invalidation import post_save_handler


class Route(models.Model):
    mother_brand = models.ForeignKey(Brand, related_name="route", on_delete=models.DO_NOTHING)

    page_type = models.CharField(verbose_name=_("Page Type"), max_length=100)
    page_role = models.CharField(verbose_name=_("Page Role"), max_length=100)

    url_format = models.CharField(verbose_name=_("URL"), max_length=100)
    redirects_to = models.ForeignKey("self", verbose_name=_("Redirect To"), null=True, blank=True)
    last_update = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.page_type


class HtmlMeta(models.Model):
    route = models.ForeignKey(Route, related_name='htmlmetas')
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    value = models.CharField(verbose_name=_("value"), max_length=300)


class RouteParam(models.Model):
    route = models.ForeignKey(Route, related_name='routeparams')
    name = models.CharField(verbose_name=_("Name"), blank=True, max_length=100)
    is_required = models.BooleanField(default=0)


@receiver(post_save, sender=Route, dispatch_uid='routes.models.Route')
def on_route_saved(sender, **kwargs):
    post_save_handler('route', sender, **kwargs)

@receiver(post_delete, sender=Route, dispatch_uid='routes.models.Route')
def on_route_deleted(sender, **kwargs):
    post_delete_handler('route', sender, **kwargs)