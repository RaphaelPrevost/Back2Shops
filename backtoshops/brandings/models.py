from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class Branding(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Slide name'))
    sort_key = models.IntegerField(verbose_name=_('Sort key'), default=1) 
    img = models.ImageField(verbose_name=_('Slide image'), upload_to="branding")
    landing_url = models.URLField(verbose_name=_('landing URL'), null=True, blank=True)
    show_from = models.DateTimeField(null=True, blank=True, verbose_name=_('Show from'))
    show_until = models.DateTimeField(null=True, blank=True, verbose_name=_('Show until'))
    
    def __unicode__(self):
        return self.name