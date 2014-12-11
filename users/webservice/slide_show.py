import logging
import urllib
import urllib2
import settings

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
            resp.body = content
            resp.content_type = "application/xml"
        except Exception, e:
            gen_xml_resp('error.xml', resp, **{'error': str(e)})
        return resp

