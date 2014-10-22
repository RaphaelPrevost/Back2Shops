import settings
import datetime
import logging
import os
import random
import ujson
import urllib
import urllib2

from B2SUtils.errors import ValidationError

def _get_mock_vessel_detail():
    return {
        'objects': [{
            'destination': 'CADIZ',
            'etatime': '2014-12-03T09:45+0000',
            'flag': 'IT|Italy',
            'heading': '87.0',
            'imonumber': 9362542,
            'last_ports': [
                {"arrival": '2014-12-03T09:45+0000',
                 "departure": '2014-12-03T11:45+0000',
                 "locode": "ESYCZ",
                 "name": "Cadiz",
                },
                {"arrival": '2014-12-02T08:56+0000',
                 "departure": '2014-12-02T15:29+0000',
                 "locode": "PTLIS",
                 "name": "Lisboa", },
            ],
            'latitude': str(random.uniform(25, 36.3424)),
            'location': 'North Atlantic Ocean, PT',
            'longitude': str(random.uniform(-15, -7.83245)),
            'mmsinumber': 247229700,
            'name': 'AIDABELLA',
            'navigationstatus': 'under way with engine',
            'photos': '//img4.fleetmon.com/thumbnails/COSCO_CHINA_41931.220x146.jpg|//img4.fleetmon.com/thumbnails/COSCO_CHINA_41931.570x1140.jpg',
            'positionreceived': str(datetime.datetime.utcnow()), #'2015-11-03T05:42+0000',
            'type': 'Passenger ship',
        }],
        "meta": {
            "limit": 5, "next": None, "offset": 0,
            "previous": None, "total_count": 2,
        }
    }

class FleetmonAPI:
    def searchVessel(self, name=None, imo=None, mmsi=None):
        kwargs = {}
        if imo:
            kwargs['imo'] = imo
        elif mmsi:
            kwargs['mmsi'] = mmsi
        elif name:
            kwargs['q'] = name
        else:
            raise ValidationError('INVALID_REQUEST')

        result = self._execute('/api/p/personal-v1/vesselurl/', **kwargs)
        objects = result['objects']

        while result['meta']['next']:
            result = self._execute(result['meta']['next'])
            objects += result['objects']
        return objects

    def getVesselInfo(self, name=None, imo=None, mmsi=None):
        kwargs = {}
        if imo:
            kwargs['imonumber'] = imo
        elif mmsi:
            kwargs['mmsinumber'] = mmsi
        elif name:
            kwargs['q'] = name
        else:
            raise ValidationError('INVALID_REQUEST')

        kwargs['lastports'] = 1
        if settings.USE_MOCK_FLEETMON_DATA:
            result = _get_mock_vessel_detail()
        else:
            result = self._execute('/api/p/personal-v1/vessels_terrestrial/',
                                   **kwargs)
            print result
        objects = result['objects']

        while result['meta']['next']:
            result = self._execute(result['meta']['next'])
            objects += result['objects']
        return objects

    def searchPort(self, name=None, country=None, locode=None):
        kwargs = {}
        if locode:
            kwargs['locode'] = locode
        elif name:
            kwargs['q'] = name
            if country:
                kwargs['country_isocode'] = country
        else:
            raise ValidationError('INVALID_REQUEST')

        result = self._execute('/api/p/personal-v1/porturl/', **kwargs)
        objects = result['objects']

        while result['meta']['next']:
            result = self._execute(result['meta']['next'])
            objects += result['objects']
        return objects

    def _execute(self, path, **kwargs):
        api_url = os.path.join(settings.FLEETMON_API_URL, path.lstrip('/'))
        if kwargs:
            kwargs.update({
                'username': settings.FLEETMON_USERNAME,
                'api_key': settings.FLEETMON_API_KEY,
                'format': 'json',
            })
            api_url += "?%s" % urllib.urlencode(kwargs)

        try:
            req = urllib2.Request(api_url)
            resp = urllib2.urlopen(req, timeout=5)
            return ujson.loads(resp.read())
        except Exception, e:
            logging.error("Got exception when accessing third-party API "
                          "(url: %s) : %s", api_url, e, exc_info=True)
            raise

