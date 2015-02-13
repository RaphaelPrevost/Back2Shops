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


import os
import re
import sys
import zipfile
from bs4 import BeautifulSoup
from pykml import parser

sys.path.append('.')
import settings
from B2SUtils import db_utils
from B2SUtils.db_utils import get_conn
from B2SUtils.db_utils import init_db_pool


def process_kmz(kmz_filename):
    with zipfile.ZipFile(kmz_filename) as kmz_zip:
        init_db_pool(settings.DATABASE)
        for fname in kmz_zip.namelist():
            if fname[-4:] == ".kml":
                process_kml(kmz_zip.read(fname))
        kmz_zip.close()


def process_kml(kml_content):
    root = parser.fromstring(kml_content)
    pmark = root.Document.Folder.Placemark
    while pmark is not None:
        mmsi = pmark.name.text
        lon, lat = pmark.Point.coordinates.text.split(',')
        detail_html = pmark.description.text
        with get_conn() as conn:
            try:
                save_vessel_data(conn, mmsi, lat, lon, detail_html)
            except Exception, e:
                conn.rollback()
                raise
        # next
        pmark = pmark.getnext()

def save_vessel_data(conn, mmsi, lat, lon, detail_html):
    soup = BeautifulSoup(detail_html)
    if soup.find(name='td'):
        time = soup.find(name='p').text
        nav_status = soup.find(name='td', text='Navigation Status').find_next().text
        heading = soup.find(name='td', text='True Heading').find_next().text
        speed = soup.find(name='td', text='Speed Over Ground').find_next().text
    else:
        info = soup.find(name='p').text.split('\n')
        time = info[0]
        nav_status = ''
        m = re.match(
            r'.* (?P<speed>\d+(\.\d+)?) heading (?P<heading>\d+(\.\d+)?) .*',
            info[1])
        if m:
            heading = m.groupdict()['heading']
            speed = m.groupdict()['speed']
        else:
            heading = None
            speed = None

    vessels = db_utils.select(conn, "vessel",
                             columns=("id", ),
                             where={'mmsi': mmsi},
                             limit=1)

    if len(vessels) > 0:
        id_vessel = vessels[0][0]
    else:
        vessel_values = {
            'mmsi': mmsi,
        }
        id_vessel = db_utils.insert(conn, "vessel",
                                    values=vessel_values, returning='id')[0]
    pos_values = {
        'id_vessel': id_vessel,
        'location': '',
        'longitude': lon,
        'latitude': lat,
        'heading': format_number(heading),
        'speed': format_number(speed),
        'time': format_text(time),
        'status': nav_status,
    }

    existings = db_utils.select(conn, "vessel_position",
                                columns=("id", ),
                                where={'id_vessel': id_vessel,
                                       'time': format_text(time)},
                                limit=1)
    if len(existings) == 0:
        print "inserting: ", pos_values
        db_utils.insert(conn, "vessel_position", values=pos_values)
    else:
        print "existing: ", pos_values


def format_text(unicode_text):
    return unicode_text.encode('utf8').strip('\n').strip()

def format_number(unicode_text):
    text = format_text(unicode_text)
    text = text.split()[0]
    try:
        float(text)
        return text
    except:
        return None


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "missing KMZ filename"
        sys.exit(1)
    else:
        kmz_filename = sys.argv[1]
        if not os.path.isfile(kmz_filename):
            print "wrong KMZ filename: ", kmz_filename
            sys.exit(1)

        process_kmz(kmz_filename)
