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


import logging
import os
from PIL import Image
import re
import string
from unidecode import unidecode
import urllib2
import urlparse

def normalize_name(name):
    name = name.decode('UTF-8')

    def strict_char(c):
        # keep Chinese
        if u'\u4e00' <= c <= u'\u9fff':
            return c
        try:
            # remove accents and decompose composition
            c = unidecode(c)
            c = ''.join(i for i in c
                        if i in string.ascii_letters or i in string.digits)
            return c.lower()
        except Exception, e:
            logging.warning("Can not normalize the character '%s' for format "
                            "url of name '%s'", c, name)
            return ''

    str_list = re.split(r' |-', name)
    str_list = map(lambda word: ''.join(map(strict_char, word)), str_list)
    str_list = filter(lambda x: x, str_list) or ['default', ]
    return '-'.join(str_list)


def get_thumbnail_url(img_url, size, front_root_uri, static_files_path):
    if not img_url: return ""

    parser = urlparse.urlparse(img_url)
    if not parser.netloc:
        return img_url
    img_path, img_name = os.path.split(parser.path)
    _img_name, _img_ext = os.path.splitext(img_name)

    new_img_name = "%s-%sx%s%s" % (_img_name, size[0], size[1], _img_ext)
    if img_path:
        new_img_name = "%s/%s"  % (img_path[1:], new_img_name)
    new_img_path = os.path.join(static_files_path, new_img_name)
    new_img_url = os.path.join(front_root_uri, new_img_name)

    if os.path.exists(new_img_path):
        return new_img_url

    directory = os.path.dirname(new_img_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        resp = urllib2.urlopen(img_url)
        img_content = resp.read()
        with open(new_img_path, 'w') as f:
            f.write(img_content)
            f.close()
        img = Image.open(new_img_path)
        img.thumbnail(size, Image.ANTIALIAS)
        img = img.convert('RGB')
        img.save(new_img_path)
    except Exception, e:
        logging.error("Failed download and resize img: %s, err: %s",
                      img_url, e, exc_info=True)
    return new_img_url

