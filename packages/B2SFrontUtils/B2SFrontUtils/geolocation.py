import logging
import os
import sys
from collections import defaultdict
from geoip2 import database
from geoip2.errors import AddressNotFoundError


def get_location_by_ip(ip):
    location = {
        'country': defaultdict(dict),
        'subdivision': defaultdict(dict),
        'city': defaultdict(dict),
        'location': defaultdict(dict),
    }
    data_dir = os.path.join(sys.prefix, 'data')
    data_file = os.path.join(data_dir, 'GeoLite2-City.mmdb')
    reader = database.Reader(data_file)
    try:
        resp = reader.city(ip)
        location['country'].update({
            'iso_code': resp.country.iso_code,
            'name': resp.country.name,
            'names': resp.country.names,
        })
        location['subdivision'].update({
            'iso_code': resp.subdivisions.most_specific.iso_code,
            'name': resp.subdivisions.most_specific.name,
            'names': resp.subdivisions.most_specific.names,
        })
        location['city'].update({
            'name': resp.city.name,
            'names': resp.city.names,
        })
        location['location'].update({
            'longitude': resp.location.longitude,
            'latitude': resp.location.latitude,
            'time_zone': resp.location.time_zone,
        })
    except AddressNotFoundError, e:
        logging.info('The ip address %s is not in geoip2\'s database', ip)
    return location



