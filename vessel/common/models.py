import copy

class BaseObj(object):
    def toDict(self):
        d = copy.deepcopy(self.__dict__)
        for k in d:
            if isinstance(d[k], BaseObj):
                d[k] = d[k].toDict()
            if isinstance(d[k], list) and len(d[k]) > 0 \
                    and isinstance(d[k][0], BaseObj):
                for index, subitem in enumerate(d[k]):
                    d[k][index] = subitem.toDict()
        return d

class VesselInfo(BaseObj):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.imo = kwargs.get('imo', '')
        self.mmsi = kwargs.get('mmsi', '')
        self.cs = kwargs.get('cs', '')
        self.type = kwargs.get('type', '')
        self.country_isocode = kwargs.get('country_isocode', '')
        self.country_name = kwargs.get('country_name', '')
        self.photos = kwargs.get('photos', [])

class VesselPos(BaseObj):
    def __init__(self, **kwargs):
        self.location = kwargs.get('location', '')
        self.longitude = kwargs.get('longitude', '')
        self.latitude = kwargs.get('latitude', '')
        self.heading = kwargs.get('heading', '')
        self.speed = kwargs.get('speed', '')
        self.time = kwargs.get('time', '')
        self.status = kwargs.get('status', '')

class VesselDetailInfo(VesselInfo):
    def __init__(self, **kwargs):
        super(VesselDetailInfo, self).__init__(**kwargs)
        self.departure_portname = kwargs.get('departure_portname', '')
        self.departure_locode = kwargs.get('departure_locode', '')
        self.departure_time = kwargs.get('departure_time', '')
        self.arrival_portname = kwargs.get('arrival_portname', '')
        self.arrival_locode = kwargs.get('arrival_locode', '')
        self.arrival_time = kwargs.get('arrival_time', '')
        self.positions = [VesselPos(**pos)
                          for pos in kwargs.get('positions', [])]

class PortInfo(BaseObj):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.locode = kwargs.get('locode', '')
        self.country_isocode = kwargs.get('country_isocode', '')
        self.country_name = kwargs.get('country_name', '')

class ContainerStatus(BaseObj):
    def __init__(self, **kwargs):
        self.status = kwargs.get('status', '')
        self.location = kwargs.get('location', '')
        self.time = kwargs.get('time', '')
        self.mode = kwargs.get('mode', '')
        self.vessel_name = kwargs.get('vessel_name', '')
        self.from_port = kwargs.get('from_port', '')
        self.to_port = kwargs.get('to_port', '')

class Ports(BaseObj):
    def __init__(self, **kwargs):
        self.first_pol = kwargs.get('first_pol', '')
        self.last_pod = kwargs.get('last_pod', '')
        self.ts_port = kwargs.get('ts_port', [])

class ContainerInfo(BaseObj):
    def __init__(self, **kwargs):
        self.container = kwargs.get('container', '')
        self.shipment_cycle = [ContainerStatus(**one)
                               for one in kwargs.get('shipment_cycle', [])]
        self.ports = Ports(**kwargs.get('ports', {}))

