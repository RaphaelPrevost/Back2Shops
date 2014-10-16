import settings
from common.models import *
from common.thirdparty import fleetmon


def getDs():
    if settings.USE_FLEETMON:
        return FleetmonDs()
    else:
        raise NotImplementedError()


class BaseDataSource(object):

    def searchVessel(self, **kwargs):
        raise NotImplementedError()

    def getVesselInfo(self, **kwargs):
        raise NotImplementedError()

    def searchPort(self, **kwargs):
        raise NotImplementedError()

class FleetmonDs(BaseDataSource):
    def __init__(self):
        self.api = fleetmon.FleetmonAPI()

    def searchVessel(self, **kwargs):
        items = self.api.searchVessel(**kwargs)
        results = []
        for item in items:
            country_isocode, country_name = item['flag'].split('|')
            results.append(
                VesselInfo(
                    name=item['name'],
                    imo=item['imo'],
                    mmsi=item['mmsi'],
                    cs='',
                    type=item['type'],
                    country_isocode=country_isocode,
                    country_name=country_name,
                ).toDict()
            )
        return results

    def getVesselInfo(self, **kwargs):
        items = self.api.getVesselInfo(**kwargs)
        results = []
        for item in items:
            country_isocode, country_name = item['flag'].split('|')
            to_port = item['last_ports'][0]
            from_port = item['last_ports'][1]
            info = VesselDetailInfo(
                    name=item['name'],
                    imo=item['imonumber'],
                    mmsi=item['mmsinumber'],
                    cs='',
                    type=item['type'],
                    country_isocode=country_isocode,
                    country_name=country_name,
                    photos=item['photos'].split('|'),

                    departure_portname=from_port['name'],
                    departure_locode=from_port['locode'],
                    departure_time=from_port['departure'],
                    arrival_portname=to_port['name'],
                    arrival_locode=to_port['locode'],
                    arrival_time=to_port['arrival'],
                    status=item['navigationstatus'],
                    positions=[{
                        'location': item['location'],
                        'longitude': item['longitude'],
                        'latitude': item['latitude'],
                        'heading': item['heading'],
                        'time': item['positionreceived'],
                    }],
                ).toDict()
            results.append(info)
        return results

    def searchPort(self, **kwargs):
        items = self.api.searchPort(**kwargs)
        results = []
        for item in items:
            results.append(
                PortInfo(
                    name=item['name'],
                    locode=item['locode'],
                    country_isocode=item['country_isocode'],
                    country_name=item['country_name'],
                ).toDict()
            )
        return results

