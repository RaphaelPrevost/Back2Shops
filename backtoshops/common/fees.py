import types
from decimal import Decimal

from common import carriers
from shippings.models import Carrier, Service

def _api_fee(carr_cls, data):
    handling_fee = Decimal(data.get('handling_fee') or 0)
    addr_orig = data.get('addr_orig')
    addr_dest = data.get('addr_dest')
    service = data.get('service')
    weight = float(data.get('weight') or 0)

    rate = carr_cls.getRate(addr_orig, addr_dest, service, weight)
    return Decimal(rate) + handling_fee

def _no_api_fee(data):
    return Decimal(data.get('ship_and_handling_fee') or 0)

def compute_fee(data):
    carrer_id = data.get('carrier')
    carr = Carrier.objects.get(pk=carrer_id)
    carr_flag = carr and carr.flag
    cls_name = carr_flag.upper() + carriers.CARRIER_CLS_SURFFIX
    cls = getattr(carriers, cls_name, None)
    if cls and type(cls) is types.ClassType:
        total_fee = _api_fee(cls, data)
    else:
        total_fee = _no_api_fee(data)
    return total_fee
