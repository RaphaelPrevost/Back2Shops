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
import logging
import os
import re
import requests
import urllib
from bs4 import BeautifulSoup

number_type_mapping = {
    'container': 'CONTAINER',
    'bill_of_landing': 'BILLOFLADING',
}

def gen_resp_soup(response):
    return BeautifulSoup(response.text.encode('utf8'))

class CosconAPI:

    def searchContainer(self, search_by=None, number=None):
        number_type = number_type_mapping[search_by]
        context = requests.session()
        init_response = self._execute(context)
        jsessionid = self._get_jsessionid(init_response)
        jsf_state = self._get_jsf_state(gen_resp_soup(init_response))

        data = self._get_common_post_data(number_type, number, jsf_state)
        post_response = self._post(context, data,
                                   number, number_type, jsessionid, jsf_state)
        return self._parse_post_response(post_response, context,
                                         number_type, number, jsessionid)

    def _post(self, context, data,
              number, number_type, jsessionid, jsf_state):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Faces-Request': 'partial/ajax',
            'Referer': settings.COSCON_CONTAINER_URL,
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        }
        cookies = {'JSESSIONID': jsessionid,
                   'number': number,
                   'numberType': number_type,
                   'language': 'en_US'}
        post_response = self._execute(context, data=data,
                                      headers=headers, cookies=cookies)
        return post_response

    def _parse_post_response(self, response, context,
                             number_type, number, jsessionid):
        if number_type == 'BILLOFLADING':
            func = self._parse_billoflanding_post_response
        else:
            func = self._parse_container_post_response
        data = func(response, context, number_type, number, jsessionid)
        return data

    def _parse_billoflanding_post_response(self, response, context,
                                           number_type, number, jsessionid):
        soup = gen_resp_soup(response)
        container_num = self._get_container_num(soup, number_type)
        result = self.searchContainer(search_by='container',
                                      number=container_num)
        end_time = self._get_endtime(soup)
        if end_time:
            result['shipment_cycle'] = [{
                'status': 'Empty Equipment Returned',
                'time': end_time,
            }]
        return result

    def _get_endtime(self, soup):
        top = soup.find(id='containerInfoByBlNum')
        rows = top.find(name='tbody').findChildren(name='tr')
        return rows[-1].findChildren(attrs={'class': 'labelTextMyFocus'})[-1].getText()

    def _parse_container_post_response(self, response, context,
                                       number_type, number, jsessionid):
        jsf_state = self._get_updated_value("javax.faces.ViewState", response)
        soup = gen_resp_soup(response)

        history = soup.find(id='cargoTrackingContainerHistory6')
        rows = history.find(name='tbody').findChildren(name='tr')
        shipment_cycle = self._get_shipment_cycle_info(rows,
                            jsf_state, context, number_type, number, jsessionid)

        prv_rows = history.find(id='Cargohistory').find(name='tbody').findChildren(name='tr')
        prv_shipment_cycle = self._get_shipment_cycle_info(prv_rows,
                            jsf_state, context, number_type, number, jsessionid,
                            current=False)

        return {'container': self._get_container_info(soup, number_type),
                'ports': self._get_ports_info(soup, number_type),
                'shipment_cycle': shipment_cycle,
                'prv_shipment_cycle': prv_shipment_cycle,
                }

    def _get_shipment_cycle_info(self, rows,
                                 jsf_state, context, number_type, number, jsessionid,
                                 current=True):
        from common.utils import format_datetime
        shipment_cycle = []
        last_vessel_info = None
        for row in rows:
            cols = row.find_all(attrs={'class': 'labelTextMyFocus'})
            if cols:
                status = cols[0].getText()
                location = cols[1].getText()
                time = cols[2].getText()
                mode = cols[3].getText().strip()
                shipment = {
                    'status': status,
                    'location': location,
                    'time': format_datetime(time, 'Hongkong', 'UTC'),
                    'mode': mode,
                }
                a_tag = cols[3].find_parent(name='a')
                if current and mode == 'Vessel' and a_tag:
                    a_id = a_tag.get('id')
                    data = self._get_common_post_data(number_type, number, jsf_state)
                    data['cntrNum'] = number
                    data['cntrStatus'] = status
                    data['containerHistorySize'] = len(rows)
                    data['containerSize'] = 1
                    data['issueTime'] = time
                    data[a_id] = a_id
                    data['javax.faces.partial.render'] = 'vesselInfoField'
                    data['javax.faces.source'] = a_id
                    data['numberType'] = number_type
                    post_response = self._post(context, data, number, number_type,
                                               jsessionid, jsf_state)
                    jsf_state = self._get_updated_value("javax.faces.ViewState",
                                                        post_response)
                    vessel_html = self._get_updated_value("vesselInfoField",
                                                          post_response)
                    vessel_info = self._parse_vessel_info(vessel_html)
                    last_vessel_info = vessel_info
                    shipment.update(vessel_info)

                if mode == '' and last_vessel_info:
                    shipment.update(last_vessel_info)

                shipment_cycle.append(shipment)

        return shipment_cycle

    def _parse_vessel_info(self, html):
        soup = BeautifulSoup(html)
        info = soup.find(id='vesselInfoField_content')
        rows = info.find(name='table').findChildren(name='tr')
        vessel_info = {
            'vessel_name': rows[0].find_all(name='td')[1].getText(),
            'from_port': rows[1].find_all(name='td')[1].getText(),
            'to_port': rows[3].find_all(name='td')[1].getText(),
        }
        return vessel_info

    def _get_container_num(self, soup, number_type):
        if number_type == 'CONTAINER':
            top = soup.find(id='CargoTracking1') \
                      .find(attrs={'class': 'Containerkuang3'})
            rows = top.find(name='table').findChildren(name='tr')
        else:
            top = soup.find(id='containerInfoByBlNum')
            rows = top.find(name='tbody').findChildren(name='tr')
        return rows[-1].find(attrs={'class': 'labelTextMyFocus'}).getText()

    def _get_container_info(self, soup, number_type):
        if number_type != 'CONTAINER': return {}

        top = soup.find(id='CargoTracking1') \
                  .find(attrs={'class': 'Containerkuang3'})
        rows = top.find(name='table').findChildren(name='tr')
        result = rows[-1].find_all(attrs={'class': 'labelTextMyFocus'})
        from common.utils import format_datetime
        return {
            'container_num': result[0].getText(),
            'container_size': result[1].getText(),
            'seal_no': result[2].getText(),
            'location': result[3].getText(),
            'status': result[4].getText(),
            'datetime': format_datetime(result[5].getText(), 'Hongkong', 'UTC'),
        }

    def _get_ports_info(self, soup, number_type):
        if number_type != 'CONTAINER': return {}

        points = soup.find(id='cargopic1')
        ports = {}
        for _name, _text in [('por', '提空点'), ('fnd', '返空点'),
                             ('first_pol', '始发港'), ('last_pod', '目的港')]:
            p = points.find(name='div', text=_text)
            if p and p.find_next():
                ports[_name] = self._get_valid_port_name(p.find_next().text)

        ports['ts_port'] = []
        for p in points.findChildren(name='div', text='中转港'):
            if p and p.find_next():
                pname = self._get_valid_port_name(p.find_next().text)
                if pname and (len(ports['ts_port']) == 0
                              or ports['ts_port'][-1] != pname):
                    ports['ts_port'].append(pname)
        return ports

    def _get_valid_port_name(self, text):
        return text.encode('utf-8').split('\n')[0].replace('·', '').strip().split(',')[0]

    def _get_jsf_state(self, soup):
        state = soup.find(id='javax.faces.ViewState')
        return state.get('value') if state else ''

    def _get_updated_value(self, name, response):
        ret = re.findall(
            r'<update id="%s"><\!\[CDATA\[(.*?)\]\]></update>' % name,
            response.text, re.M|re.S)
        return ret[0]

    def _get_jsessionid(self, response):
        return response.cookies.get('JSESSIONID') or ''

    def _execute(self, context, data=None, headers=None, cookies=None):
        try:
            api_url = settings.COSCON_CONTAINER_URL
            if data:
                data = urllib.urlencode(data)
                response = context.post(api_url, data=data,
                                  timeout=settings.THIRDPARTY_ACCESS_TIMEOUT,
                                  headers=headers, cookies=cookies)
            else:
                response = context.get(api_url,
                                  timeout=settings.THIRDPARTY_ACCESS_TIMEOUT)
            return response
        except Exception, e:
            logging.error("Got exception when accessing third-party API "
                          "(url: %s) : %s", api_url, e, exc_info=True)
            raise

    def _get_common_post_data(self, number_type, number, jsf_state):
        return {
            'a10time1': '',
            'a10time2': '',
            'a11time1': '',
            'a11time2': '',
            'a12time': '',
            'a13time': '',
            'a2time': '',
            'a3time': '',
            'a5time1': '',
            'a5time2': '',
            'a7time1': '',
            'a7time2': '',
            'a9time1': '',
            'a9time2': '',
            'billRemark': '',
            'bkRmark': '',
            'bookingNumbers': '0',
            'cargoTrackSearchId': number_type,
            'cargoTrackingPara': number,
            'cargoTrackingRedirect': 'false',
            'cargoTrckingFindButton': 'cargoTrckingFindButton',
            'cntrOrderType': '',
            'cntrOrderType2': '',
            'cntrRemark': '',
            'containerNumberAll': '',
            'containerNumberAllByBookingNumber': '',
            'containerSize': '',
            'containerTransportationMode': '',
            'isbillOfLadingExist': 'false',
            'isbookingNumberExist': 'false',
            'j_idt1189': '',
            'j_idt172': '',
            'j_idt636': '',
            'j_idt665': '',
            'j_idt694': '',
            'j_idt723': '',
            'j_idt752': '',
            'javax.faces.ViewState': jsf_state,
            'javax.faces.partial.ajax': 'true',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'bookingNumbers billToBookingGrop billofLading_Table3 release_Information_bill release_Information_booking cargoTrackingOrderBillInformation cargoTrackingBookingOfLadingInformation cargoTrackingContainerHistory cargoTrackingContainerInfoStatus cargoTrackingContainerBillOfLadingNumber1 cargoTrackingContainerInfoByContainerNumber release_Information_booking_version release_Information_bill_version actualLoadingInfo containerInfoByBlNum containerInfoByBkgNumTable actualLoadingInfo5 documentStatus cargoTrackingAcivePictures containerNumberAll containerInfo_table3 containerInfo_table4 cargoTrackingPrintByContainer containerNumberAllByBookingNumber registerUserValidate validateCargoTracking isbillOfLadingExist isbookingNumberExist cargoTrackingContainerPictureByContainer cargoTrackingContainerHistory1 cargoTrackingOrderBillMyFocus cargoTrackingBookingMyFocus userId contaienrNoExist billChange4 bookingChange4 bookingChange3 cargoTrackingContainerHistory6 numberType containerSize containerMessage containerTab isLogin cargoTrackingBillContainer cargoTrackingBillContainer1 BillMessage BookingMessage searchSuccess searchError containerTransportationMode',
            'javax.faces.source': 'cargoTrckingFindButton',
            'mainForm': 'mainForm',
            'num': '0',
            'num1': '0',
            'num2': '0',
            'num3': '0',
            'num4': '0',
            'num5': '0',
            'num6': '0',
            'numberType': '',
            'onlyFirstAndLast': 'false',
            'onlyFirstAndLast2': 'false',
            'userId': '',
            'validateCargoTracking': 'false',
        }

