# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


from django.db import models
from django.utils.translation import ugettext_lazy as _


class Event(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=50)
    desc = models.CharField(verbose_name=_("Description"), max_length=100)
    handler_url = models.CharField(verbose_name=_("Handler URL"), blank=True, max_length=100)
    handler_method = models.CharField(verbose_name=_("Handler method"), default='post', blank=True, max_length=10)
    handler_is_private = models.BooleanField(default=True)
    predefined_subject = models.TextField(blank=True, default='')
    predefined_template = models.TextField(blank=True, default='')

class EventHandlerParam(models.Model):
    event = models.ForeignKey(Event, related_name='event_handler_params')
    name = models.CharField(verbose_name=_("Param Name"), max_length=50)
    value = models.CharField(verbose_name=_("Param Value"), null=True, max_length=50)

class EventQueue(models.Model):
    event = models.ForeignKey(Event)
    param_values = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)
    error = models.TextField()

