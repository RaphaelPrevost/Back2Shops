# coding:UTF-8
from django.db import models


class Visitors(models.Model):
    sid = models.CharField(max_length=36, primary_key=True)
    users_id = models.IntegerField(blank=True, null=True)
    visit_time = models.DateTimeField(blank=False, null=False)

    def __unicode__(self):
        return str(self.sid) + '-' + str(self.users_id)
