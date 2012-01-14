from django.db import models

SETTING_KEY_CHOICES = (
                       ('default_language','default language'),
                       ('default_currency','default currency')
                       )

# Create your models here.
class GlobalSettings(models.Model):
    key = models.CharField(max_length=200,primary_key=True,choices=SETTING_KEY_CHOICES)
    value = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.key