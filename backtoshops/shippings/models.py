from django.db import models

class Carrier(models.Model):
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=50)
    carrier = models.ForeignKey(Carrier, related_name='services')

    def __unicode__(self):
        return self.carrier.name + ' - ' + self.name
