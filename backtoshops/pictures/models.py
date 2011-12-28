from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from sorl.thumbnail import ImageField

class ProductPicture(models.Model):
    picture = ImageField(upload_to="product_pictures")
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")

    def __unicode__(self):
        return self.picture.url
