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