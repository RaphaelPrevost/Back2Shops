import falcon

class Response(falcon.response.Response):
    def __init__(self):
        super(Response, self).__init__()
        self.extra_headers = list()

    def append_header(self, name, value):
        '''Fixes the problem of multiple Cookie headers.
            @input 
                name, value

            usage:
                resp.append_header('set-cookie', 'session-id=321654987654')
        '''
        self.extra_headers.append((name, value))

    def _wsgi_headers(self, media_type=None):
        header_list = super(Response, self)._wsgi_headers(media_type=media_type)
        for key, header in enumerate(header_list):
            if isinstance(header[1], list):
                header_list.pop(key)
                for val in header[1]:
                    header_list.append((header[0], val))

        return header_list + self.extra_headers


falcon.api.Response = Response