import json
from django.http import HttpResponse
from countries.models import CaProvince
from countries.models import UsState


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
                states_list.append({'label': state.name, 'value': state.name})
    return HttpResponse(json.dumps(states_list), mimetype='application/json')
