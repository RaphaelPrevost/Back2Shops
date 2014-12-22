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


import logging
import ujson
import urllib
import urllib2
import settings
import xmltodict

from B2SRespUtils.generate import gen_xml_resp

class BaseProxy(object):
    api_path = None
    def bo_proxy(self, api_path, data=None, headers={}, **query):
        remote_url = settings.SALES_SERVER_API_URL % {'api': api_path}
        if query:
            query_str = urllib.urlencode(query)
            remote_url = "?".join([remote_url, query_str])
        req = urllib2.Request(remote_url, data=data, headers=headers)
        try:
            resp = urllib2.urlopen(req)
            return resp.read()
        except urllib2.HTTPError, e:
            logging.error('get_from_remote HTTPError: '
                          'error: %s, '
                          'with uri: %s, data :%s, headers: %s'
                          % (e, remote_url, data, headers), exc_info=True)
            raise




class SlideShowResource(BaseProxy):
    api_path = "/webservice/1.0/pub/brand/home/slideshow/%s"

    def on_get(self, req, resp, **kwargs):
        try:
            brand = req.get_param('brand')
            assert brand is not None, 'Missing brand'

            api_path = self.api_path % brand
            content = self.bo_proxy(api_path)
            slides = xmltodict.parse(content)
            resp.body = ujson.dumps(slides)
            resp.content_type = "application/json"
        except Exception, e:
            gen_xml_resp('error.xml', resp, **{'error': str(e)})
        return resp

