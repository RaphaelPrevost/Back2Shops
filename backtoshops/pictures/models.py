from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from sorl.thumbnail import ImageField
from common.assets_utils import AssetsStorage

class ProductPicture(models.Model):
    picture = ImageField(upload_to="img/product_pictures",
                         storage=AssetsStorage())
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")

    def __unicode__(self):
        return self.picture.url
