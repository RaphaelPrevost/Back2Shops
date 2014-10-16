import copy

class BaseVesselObj(object):
    def toDict(self):
        d = copy.deepcopy(self.__dict__)
        for k in d:
            if isinstance(d[k], BaseVesselObj):
                d[k] = d[k].toDict()
            if isinstance(d[k], list) and len(d[k]) > 0 \
                    and isinstance(d[k][0], BaseVesselObj):
                for index, subitem in enumerate(d[k]):
                    d[k][index] = subitem.toDict()
        return d

class VesselInfo(BaseVesselObj):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.imo = kwargs.get('imo', '')
        self.mmsi = kwargs.get('mmsi', '')
        self.cs = kwargs.get('cs', '')
        self.type = kwargs.get('type', '')
        self.country_isocode = kwargs.get('country_isocode', '')
        self.country_name = kwargs.get('country_name', '')
        self.photos = kwargs.get('photos', [])

class VesselPos(BaseVesselObj):
    def __init__(self, **kwargs):
        self.location = kwargs.get('location', '')
        self.longitude = kwargs.get('longitude', '')
        self.latitude = kwargs.get('latitude', '')
        self.heading = kwargs.get('heading', '')
        self.time = kwargs.get('time', '')

class VesselDetailInfo(VesselInfo):
    def __init__(self, **kwargs):
        super(VesselDetailInfo, self).__init__(**kwargs)
        self.departure_portname = kwargs.get('departure_portname', '')
        self.departure_locode = kwargs.get('departure_locode', '')
        self.departure_time = kwargs.get('departure_time', '')
        self.arrival_portname = kwargs.get('arrival_portname', '')
        self.arrival_locode = kwargs.get('arrival_locode', '')
        self.arrival_time = kwargs.get('arrival_time', '')
        self.status = kwargs.get('status', '')
        self.positions = [VesselPos(**pos)
                          for pos in kwargs.get('positions', [])]

class PortInfo(BaseVesselObj):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.locode = kwargs.get('locode', '')
        self.country_isocode = kwargs.get('country_isocode', '')
        self.country_name = kwargs.get('country_name', '')

