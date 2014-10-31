import settings
from common.models import *
from common.thirdparty import coscon
from common.thirdparty import fleetmon


def getVesselDs():
    if settings.USE_FLEETMON:
        return FleetmonDs()
    else:
        raise NotImplementedError()

def getContainerDs():
    if settings.USE_COSCON_CONTAINER:
        return CosconDs()
    else:
        raise NotImplementedError()

class BaseDataSource(object):

    def searchVessel(self, **kwargs):
        raise NotImplementedError()

    def getVesselInfo(self, **kwargs):
        raise NotImplementedError()

    def searchPort(self, **kwargs):
        raise NotImplementedError()

    def searchContainer(self, **kwargs):
        raise NotImplementedError()


class CosconDs(BaseDataSource):
    def __init__(self):
        self.api = coscon.CosconAPI()

    def searchContainer(self, **kwargs):
        data = self.api.searchContainer(**kwargs)
        return ContainerInfo(**data).toDict()


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
            if len(item['last_ports']) > 0:
                from_port = item['last_ports'][0]
            else:
                from_port = {}
            info = VesselDetailInfo(
                    name=item['name'],
                    imo=item['imonumber'],
                    mmsi=item['mmsinumber'],
                    cs='',
                    type=item['type'],
                    country_isocode=country_isocode,
                    country_name=country_name,
                    photos=item['photos'].split('|'),

                    departure_portname=from_port.get('portname'),
                    departure_locode=from_port.get('locode'),
                    departure_time=from_port.get('departure'),
                    arrival_portname=item['destination'],
                    arrival_locode=item['destination'],
                    arrival_time=item['etatime'],
                    positions=[{
                        'location': item['location'],
                        'longitude': item['longitude'],
                        'latitude': item['latitude'],
                        'heading': item['heading'],
                        'speed': None,
                        'time': item['positionreceived'],
                        'status': item['navigationstatus'],
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

