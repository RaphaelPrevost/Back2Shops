# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


import json
from django.forms.widgets import TextInput
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from multiwidgetlayout.widgets import MultiWidgetLayout

class ScheduleWidget(MultiWidgetLayout):

        is_localized = True        

	def __init__(self, attrs=None):
		days = [
			_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"),
			_("Friday"), _("Saturday"), _("Sunday")
		]
		layout = []
		for i in days:
			layout += [
				"<label for='%(id)s'>", unicode(i), "</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> ", unicode(_("and")), " </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
			]
		super(ScheduleWidget, self).__init__(layout, attrs)

	def decompress(self, value):
		toret = []
                # XXX force the widget to update the translation
                self.__init__()
		if value:
			data = json.loads(value)
			if data:
				for i in xrange(7):
					toret.append(data[str(i)]['am']['open'])
					toret.append(data[str(i)]['am']['close'])
					toret.append(data[str(i)]['pm']['open'])
					toret.append(data[str(i)]['pm']['close'])
				return toret
		return []
