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
