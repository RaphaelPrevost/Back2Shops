# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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

import ais
import os
import sys
import time

sys.path.append('.')
import settings
from B2SUtils import db_utils
from B2SUtils.db_utils import get_conn
from B2SUtils.db_utils import init_db_pool
from common.constants import VESSEL_STATUS

nav_status_mapping = {
    0: VESSEL_STATUS.UNDER_WAY_USING_ENGINE,
    1: VESSEL_STATUS.AT_ANCHOR,
    2: VESSEL_STATUS.NOT_UNDER_COMMAND,
    3: VESSEL_STATUS.SPECIAL_POS_REPORT,
    5: VESSEL_STATUS.MOORED,
}

ship_type_mapping = {
    69: 'Passenger, No additional information',
    70: 'Cargo, all ships of this type',
    71: 'Cargo, Hazardous category A',
    72: 'Cargo, Hazardous category B',
    73: 'Cargo, Hazardous category C',
    74: 'Cargo, Hazardous category D',
    79: 'Cargo, No additional information'
}

def extract_advdm_info(msgs, msg_type):
    aismsg = ''
    for idx, msg in enumerate(msgs):
        nmeamsg = msg.split(',')
        if nmeamsg[0] != '!AIVDM':
            raise Exception('Wrong message: %s' % msg)
        assert int(nmeamsg[1]) == len(msgs)
        assert int(nmeamsg[2]) == idx + 1

        aismsg += nmeamsg[5]
        checksum = nmeamsg[6]

    return decode_advdm(aismsg, msg_type)

def decode_advdm(aismsg, msg_type):
    bv = ais.binary.ais6tobitvec(aismsg)
    return getattr(ais, 'ais_msg_%s' % msg_type, 'ais_msg_1').decode(bv)

def extract_extra_info(msg):
    info = {}
    msg, checksum = msg.split('*')
    for one in msg.split(','):
        if one.startswith('s:'):
            info['source'] = one[2:]
        elif one.startswith('c:'):
            info['time'] = format_epoch_time(int(one[2:]))
        elif one.startswith('g:'):
            info['index'], info['total'], info['id'] = one[2:].split('-')
            info['index'] = int(info['index'])
            info['total'] = int(info['total'])
    return info

def format_epoch_time(seconds, format='%Y-%m-%d %H:%M'):
    return time.strftime(format, time.gmtime(seconds))

def process_file(filename):
    with open(filename) as f:
        init_db_pool(settings.DATABASE)
        line = f.readline()
        while line:
            data = {}
            advdm_msgs = []
            while True:
                _, extra_msg, advdm_msg = line.split('\\')
                info = extract_extra_info(extra_msg)
                data.update(info)
                advdm_msgs.append(advdm_msg)
                if 'total' in info and info['index'] < info['total']:
                    line = f.readline()
                else:
                    break

            data['ais_pos'] = extract_advdm_info(advdm_msgs, 1)
            if len(advdm_msgs) > 1:
                data['ais_ship'] = extract_advdm_info(advdm_msgs, 5)

            with get_conn() as conn:
                try:
                    save_vessel_data(conn, data)
                except Exception, e:
                    conn.rollback()
                    raise

            # next
            line = f.readline()


def save_vessel_data(conn, data):
    time = data['time']
    ais_pos = data['ais_pos']
    mmsi = str(ais_pos['UserID'])
    lon = ais_pos['longitude']
    lat = ais_pos['latitude']
    heading = ais_pos['TrueHeading']
    speed = ais_pos['SOG']
    nav_status = nav_status_mapping.get(ais_pos['NavigationStatus'],
                                        ais_pos['NavigationStatus'])

    vessel_values = {
        'mmsi': mmsi,
    }
    if 'ais_ship' in data:
        ais_ship = data['ais_ship']
        vessel_values.update({
            'name': ais_ship['name'].strip(),
            'imo': ais_ship['IMOnumber'],
            'cs': ais_ship['callsign'],
            'type': ship_type_mapping.get(ais_ship['shipandcargo'],
                                          ais_ship['shipandcargo']),
        })

    vessels = db_utils.select(conn, "vessel",
                             columns=("id", ),
                             where={'mmsi': mmsi},
                             limit=1)
    if len(vessels) > 0:
        id_vessel = vessels[0][0]
        db_utils.update(conn, "vessel", values=vessel_values)
    else:
        id_vessel = db_utils.insert(conn, "vessel",
                                    values=vessel_values, returning='id')[0]
    pos_values = {
        'id_vessel': id_vessel,
        'location': '',
        'longitude': lon,
        'latitude': lat,
        'heading': heading,
        'speed': speed,
        'time': time,
        'status': nav_status,
    }

    existings = db_utils.select(conn, "vessel_position",
                                columns=("id", ),
                                where={'id_vessel': id_vessel,
                                       'time': time},
                                limit=1)
    if len(existings) == 0:
        print "inserting: ", pos_values
        db_utils.insert(conn, "vessel_position", values=pos_values)
    else:
        print "existing: ", pos_values


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "missing NMEA filename"
        sys.exit(1)
    else:
        filename = sys.argv[1]
        if not os.path.isfile(filename):
            print "wrong NMEA filename: ", filename
            sys.exit(1)

        process_file(filename)

