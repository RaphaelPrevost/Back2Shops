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


from urllib2 import HTTPError, URLError
from sorl.thumbnail.base import ThumbnailBackend as _ThumbnailBackend
from sorl.thumbnail import base
from common.assets_utils import get_full_url


patched = {}
class CustomThumbnailBackend(_ThumbnailBackend):
    def get_thumbnail(self, file, geometry_string, **options):
        try:
            thumbnail = super(CustomThumbnailBackend, self).get_thumbnail(file, geometry_string, **options)
            if not thumbnail.exists():
                super(CustomThumbnailBackend, self).delete(thumbnail)
                thumbnail = super(CustomThumbnailBackend, self).get_thumbnail(file, geometry_string, **options)
        except (HTTPError, URLError), e:
            file = get_full_url('img/product_pictures/default_img.png')
            thumbnail = super(CustomThumbnailBackend, self).get_thumbnail(file, geometry_string, **options)

        return thumbnail

def monkey_patch_for_thumbnail():
    global patched
    patched['thumbnail'] = True
    base.ThumbnailBackend = CustomThumbnailBackend

def monkey_patch():
    global patched
    if not patched.get('thumbnail'):
        monkey_patch_for_thumbnail()
