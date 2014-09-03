from django.db import models
from sorl.thumbnail import ImageField

from common.assets_utils import AssetsStorage

class EmailTemplate(models.Model):
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=200)
    html_head = models.TextField(default='')
    html_body = models.TextField(default='')

class EmailTemplateImage(models.Model):
    email = models.ForeignKey("EmailTemplate", related_name="images", null=True, blank=True)
    image = ImageField(upload_to="img/email_images",
                       storage=AssetsStorage())

