import json
from django import forms
from django.utils.datastructures import SortedDict
from shops.models import Shop
from widgets import ScheduleWidget

class ScheduleField(forms.MultiValueField):
	widget = ScheduleWidget()

	def __init__(self, *args, **kwargs):
		fields = []
		for i in xrange(7*2*2):
			fields.append(forms.CharField())
		super(ScheduleField, self).__init__(fields, *args, **kwargs)

	def compress(self, data_list):
		toret = SortedDict()
		if data_list:
			for i, j in enumerate(xrange(0, 7*2*2, 4)):
				toret[i] = {
					'am': {'open': data_list[j], 'close': data_list[j+1]},
					'pm': {'open': data_list[j+2], 'close': data_list[j+3]}
				}
		return json.dumps(toret)


class ShopForm(forms.ModelForm):
	error_css_class = 'error'
	required_css_class = 'required'
	class Meta:
		model = Shop
		#exclude = ("opening_hours",)

	def __init__(self, *args, **kwargs):
		super(ShopForm, self).__init__(*args, **kwargs)
		self.fields['upc'].widget = forms.TextInput(attrs={'class': 'inputM'})
		self.fields['zipcode'].widget = forms.TextInput(attrs={'class': 'inputXS'})
		self.fields['phone'].widget = forms.TextInput(attrs={'class': 'inputS'})
		self.fields['city'].widget = forms.TextInput(attrs={'class': 'inputM'})
		self.fields['description'].widget = forms.Textarea(attrs={"cols": 30, "rows": 4})
		self.fields['latitude'].widget = forms.HiddenInput()
		self.fields['longitude'].widget = forms.HiddenInput()
		self.fields['mother_brand'].widget = forms.HiddenInput()
		self.fields['opening_hours'] = ScheduleField(required=False)
