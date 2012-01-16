import json
from django.forms.widgets import TextInput
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from multiwidgetlayout.widgets import MultiWidgetLayout

class ScheduleWidget(MultiWidgetLayout):
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
