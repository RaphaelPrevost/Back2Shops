# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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
        "meta": {
            "cp_consumed": 1.5, "cp_remaining": 96.0, "limit": 5,
            "next": None, "offset": 0, "previous": None, "total_count": 1},
        "objects": [{
            "destination": "BAR HARBOR",
            "etatime": "2014-10-28T11:00+0000",
            "flag": "IT|Italy",
            "heading": "307.0",
            "imonumber": 9362542,
            "last_ports": [{
                "arrival": "2014-10-21T12:37+0000",
                "departure": "2014-10-23T18:08+0000",
                "locode": "CAMTR",
                "portname": "Montreal"
            }, {
                "arrival": "2014-10-27T10:10+0000",
                "departure": "2014-10-27T17:50+0000",
                "locode": "CAHAL",
                "portname": "Halifax"
            }],
            "latitude": str(random.uniform(25, 43.628562)),
            "location": "Gulf of Maine, CA",
            "longitude": str(random.uniform(-30, -66.714317)),
            "mmsinumber": 247229700,
            "name": "AIDABELLA",
            "navigationstatus": "under way using engine",
            "photos": "//img3.fleetmon.com/thumbnails/AIDABELLA_603862.220x146.jpg|//img3.fleetmon.com/thumbnails/AIDABELLA_603862.570x1140.jpg", 
            "positionreceived": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M+0000'),
            "publicurl": "http://www.fleetmon.com/en/vessels/Aidabella_50934",
            "type": "Passenger ship"}
        ]}


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
            resp = urllib2.urlopen(req,
                         timeout=settings.THIRDPARTY_ACCESS_TIMEOUT)
            json_return = ujson.loads(resp.read())
            logging.info('Got return from Fleetmon (url: %s) : \n%s',
                         api_url, json_return)
            return json_return
        except Exception, e:
            logging.error("Got exception when accessing third-party API "
                          "(url: %s) : %s", api_url, e, exc_info=True)
            raise

