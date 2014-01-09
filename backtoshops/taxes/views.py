import json
from django.db.models import Q
from django.http import HttpResponse
from taxes.models import Rate


def get_rates(request, *args, **kwargs):
    rates_list = []
    region_id = kwargs.get('rid', None)
    rates = Rate.objects.filter(region_id=region_id)

    province_name = request.GET.get('pname', None)
    if province_name:
        rates = rates.filter(
            Q(province='') | Q(province=province_name)
        )
    else:
        rates = rates.filter(province='')

    shipping_to_region_id = request.GET.get('srid', None)
    if shipping_to_region_id:
        rates = rates.filter(
            Q(shipping_to_region_id__isnull=True) |
            Q(shipping_to_region_id=shipping_to_region_id)
        )
    else:
        rates = rates.filter(shipping_to_region_id__isnull=True)

    shipping_to_province_name = request.GET.get('spname', None)
    if shipping_to_province_name:
        rates = rates.filter(
            Q(shipping_to_province='') |
            Q(shipping_to_province=shipping_to_province_name)
        )
    else:
        rates = rates.filter(shipping_to_province='')

    for rate in rates:
        rates_list.append({'label': str(rate), 'value': rate.id})
    return HttpResponse(json.dumps(rates_list), mimetype='application/json')
