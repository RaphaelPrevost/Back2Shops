from django import forms
from routes.models import HtmlMeta, Route, RouteParam


class HTMLMetasForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputM'}))
    value = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputL'}))

    class Meta:
        model = HtmlMeta


class RouteParamForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputM'}))
    is_required = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'is_required'}))

    class Meta:
        model = RouteParam

    def __init__(self, request=None, *args, **kwargs):
        super(RouteParamForm, self).__init__(*args, **kwargs)
        self.fields['is_required'].initial = False


class RouteForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    page_type = forms.CharField()
    page_role = forms.CharField()
    url_format = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    class Meta:
        model = Route
        exclude = ('mother_brand')

    def __init__(self, request=None, *args, **kwargs):
        super(RouteForm, self).__init__(*args, **kwargs)
        self.request = request

        # populate redirects field
        mother_brand_id = self.request.user.get_profile().work_for
        route_id = self.initial.get('id')

        # remove initial slash
        if self.initial.get('url_format', ' ')[0] == '/':
            self.initial['url_format'] = self.initial['url_format'][1:]

        # populate the routes
        datas = [(x.pk, x.page_type) for x in Route.objects.filter(mother_brand_id=mother_brand_id).exclude(id=route_id)]
        datas = [('', '---------')] + datas
        self.fields['redirects_to'].choices = datas

    def edit(self, request=None, *args,  **kwargs):
        raise Exception('edit')

    def save(self, commit=True):
        route = super(RouteForm, self).save(commit=False)
        route.mother_brand = self.request.user.get_profile().work_for

        # append slash if not exists
        if route.url_format[0] != '/':
            route.url_format = '/' + route.url_format

        if commit:
            route.save()

        return route
