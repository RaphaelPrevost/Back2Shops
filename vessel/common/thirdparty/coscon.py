import settings
import logging
import os
import requests
import urllib
from bs4 import BeautifulSoup

number_type_mapping = {
    'container': 'CONTAINER',
    'bill_of_landing': 'BILLOFLADING',
}

class CosconAPI:

    def searchContainer(self, search_by=None, number=None):
        number_type = number_type_mapping[search_by]
        context = requests.session()
        init_response = self._execute(context)
        jsessionid = self._get_jsessionid(init_response)
        jsf_state = self._get_jsf_state(init_response)

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
        data = self._gen_post_data(number_type, number, jsf_state)
        post_response = self._execute(context,
                      data=data, headers=headers, cookies=cookies)
        return self.parse_post_response(post_response)

    def parse_post_response(self, response):
        soup = BeautifulSoup(response.text.encode('utf8'))
        history = soup.find(id='cargoTrackingContainerHistory')
        rows = history.find(name='tbody').findChildren(name='tr')
        shipment_cycle = []
        for row in rows:
            cols = [col.getText() for col in row.find_all(attrs={'class': 'labelTextMyFocus'})]
            if cols:
                shipment_cycle.append({
                    'status': cols[0],
                    'location': cols[1],
                    'time': cols[2], #TODO: convert timezone
                    'mode': cols[3],
                })
        return {'shipment_cycle': shipment_cycle}

    def _get_jsf_state(self, response):
        soup = BeautifulSoup(response.text.encode('utf8'))
        state = soup.find(id='javax.faces.ViewState')
        return state.get('value') if state else ''

    def _get_jsessionid(self, response):
        return response.cookies.get('JSESSIONID') or ''

    def _execute(self, context, data=None, headers=None, cookies=None):
        try:
            api_url = settings.COSCON_CONTAINER_URL
            if data:
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

    def _gen_post_data(self, number_type, number, jsf_state):
        return urllib.urlencode({
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
        })

