import json
from django.http import HttpResponse
from countries.models import CaProvince
from countries.models import CountryXCurrency
from countries.models import UsState
from sales.models import ProductCurrency


COUNTRY_STATE_MODEL_MAP = {
    'US': UsState,
    'CA': CaProvince,
}


def get_country_states(request, *args, **kwargs):
    states_list = []
    country_iso = kwargs.get('cid', None)
    if country_iso:
        state_model = COUNTRY_STATE_MODEL_MAP.get(country_iso, None)
        if state_model:
            states = state_model.objects.all()
            for state in states:
                states_list.append({'label': state.name, 'value': state.abbrev})
    return HttpResponse(json.dumps(states_list), mimetype='application/json')

def get_country_x_currency(request, *args, **kwargs):
    product_currencies = ProductCurrency.objects.all().values_list('code',
                                                                   flat=True)
    mapping = {}
    for country, currency in CountryXCurrency.objects.all().values_list(
                                                'country_id', 'currency'):
        if currency in product_currencies and country not in mapping:
            mapping[country] = currency
    return HttpResponse(json.dumps(mapping), mimetype='application/json')

