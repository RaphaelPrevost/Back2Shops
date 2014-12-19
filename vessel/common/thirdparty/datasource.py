# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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
        curr_navi = []
        last_navi = []
        for item in items:
            country_isocode, country_name = item['flag'].split('|')
            if len(item['last_ports']) > 0:
                from_port = item['last_ports'][-1]
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
                    arrival_portname='',
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
            curr_navi.append(info)

            if len(item['last_ports']) >= 2:
                from_port = item['last_ports'][-2]
                to_port = item['last_ports'][-1]
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
                        arrival_portname=to_port.get('destination'),
                        arrival_locode=to_port.get('locode'),
                        arrival_time=to_port.get('arrival'),
                        positions=[],
                    ).toDict()
            last_navi.append(info)
        return curr_navi, last_navi

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

