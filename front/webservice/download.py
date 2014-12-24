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


import os
import falcon
import logging
import settings

class Item(object):
    storage_path = settings.STATIC_FILES_PATH + '/'

    def on_get(self, req, resp, name, subpath=None):
        if subpath:
            path = os.path.join(self.storage_path, subpath, name)
        else:
            path = os.path.join(self.storage_path, name)
        try:
            resp.stream = open(path, 'rb')
            resp.stream_len = os.path.getsize(path)
            resp.content_type = self._get_media_type(name)
        except IOError, e:
            logging.error("%s", e, exc_info=True)
            resp.status = falcon.HTTP_404

    def _get_media_type(self, name):
        raise NotImplementedError

class JsItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/js/'

    def _get_media_type(self, name):
        return 'application/javascript'

class CssItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/css/'

    def _get_media_type(self, name):
        return 'text/css'

class ImgItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/img/'

    def _get_media_type(self, name):
        ext = os.path.splitext(name)[1][1:]
        return 'image/%s' % ext


class AssetItem(Item):
    storage_path = 'views/templates/%s/%s/%s'

    def on_get(self, req, resp, **kwargs):
        theme = kwargs.get('theme')
        file_type = kwargs.get('file_type')
        folder = kwargs.get('folder')
        name = kwargs.get('name')
        if folder:
            name = '%s/%s' % (folder, name)

        try:
            resp.content_type = self._get_media_type(file_type, name)

            if resp.content_type is not None:
                path = self.storage_path % (theme, file_type, name)
                resp.stream = open(path, 'rb')
                resp.stream_len = os.path.getsize(path)
        except IOError, e:
            raise e

    def _get_media_type(self, file_type, name):
        if file_type == 'js':
            return 'text/javascript'
        elif file_type == 'css':
            return 'text/css'
        elif file_type == 'img':
            ext = os.path.splitext(name)[1][1:]
            return 'image/%s' % ext
        return None
