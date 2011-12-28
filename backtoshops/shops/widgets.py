import json
from django.forms.widgets import TextInput
from django.utils.datastructures import SortedDict
from multiwidgetlayout.widgets import MultiWidgetLayout

class ScheduleWidget(MultiWidgetLayout):
	def __init__(self, attrs=None):
		days = [
			"Monday", "Tuesday", "Wednesday", "Thursday",
			"Friday", "Saturday", "Sunday"
		]
		layout = []
		for i in days:
			layout += [
				"<label for='%(id)s'>"+i+"</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
			]
		# layout = [
		# 	"<label for='%(id)s'>Monday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Tuesday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Wednesday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Thursday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Friday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Saturday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# 	"<label for='%(id)s'>Sunday</label>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}), "<span> and </span>", TextInput(attrs={"class": "inputXS"}), TextInput(attrs={"class": "inputXS"}),
		# ]
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
