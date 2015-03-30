#!/usr/bin/python
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


import argparse
import time
from slimit import minify

import sys
sys.path.append('.')
import settings

LOCAL_STATIC_PATH = 'static'

js_files = {
    'breuer': {
        '1': [
            '%s/js/jquery-1.10.2.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery-ui-1.10.4.min.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery.flexslider-min.js' % LOCAL_STATIC_PATH,
            '%s/js/easyzoom.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery.simpleGal.js' % LOCAL_STATIC_PATH,
            '%s/js/utils.js' % LOCAL_STATIC_PATH,
        ],
    },
    'dragondollar': {
        '1': [
            '%s/js/jquery-1.10.2.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery-ui-1.10.4.min.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery-migrate-1.2.1.min.js' % LOCAL_STATIC_PATH,
            '%s/js/easySlider1.7.js' % LOCAL_STATIC_PATH,
            '%s/js/utils.js' % LOCAL_STATIC_PATH,
        ],
        '2': [
            '%s/js/jquery.touchSwipe.min.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery.movingboxes.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery.maphilight.js' % LOCAL_STATIC_PATH,
            '%s/js/fancybox/jquery.mousewheel-3.0.4.pack.js' % LOCAL_STATIC_PATH,
            '%s/js/fancybox/jquery.fancybox-1.3.4.pack.js' % LOCAL_STATIC_PATH,
        ],
    },
    'vessel': {
        '1': [
            '%s/js/jquery-1.10.2.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery-ui-1.10.4.min.js' % LOCAL_STATIC_PATH,
            '%s/js/quicksilver.js' % LOCAL_STATIC_PATH,
            '%s/js/jquery.quickselect.js' % LOCAL_STATIC_PATH,
            '%s/js/utils.js' % LOCAL_STATIC_PATH,
            '%s/js/main.js' % settings.TEMPLATE_PATH[0],
        ],
    },
}


def _get_js_suffix_filename(brand, base_path=LOCAL_STATIC_PATH):
    return "%s/js/%s.suffix" % (base_path, brand)

def _get_js_min_filename(brand, section, suffix, base_path=LOCAL_STATIC_PATH):
    return "%s/js/%s_%s_%s.min.js" % (base_path, brand, section, suffix)


def _get_loader_js(src_path):
    path = src_path[src_path.index('/'):]
    js = '<script type="text/javascript" src="%s"></script>'
    return js % path

suffix = None
def get_loader_js(brand):
    global suffix
    if not suffix:
        _fname = _get_js_suffix_filename(brand)
        try:
            with open(_fname) as f:
                suffix = f.read()
        except:
            pass

    lines = []
    for section, src_paths in js_files[brand].iteritems():
        if suffix:
            min_path = _get_js_min_filename(brand, section, suffix)
            lines.append(_get_loader_js(min_path))
        else:
            for src_path in src_paths:
                lines.append(_get_loader_js(src_path))

    return '\n'.join(lines)


def minify_func(src_text):
    return minify(src_text, mangle=True)

def process_files(proc_func, src_paths, dest_path):
    print "Combining to %s" % dest_path

    with open(dest_path, 'w') as output_file:
        for src_path in src_paths:
            print "    %s" % src_path
            with open(src_path) as input_file:
                text = input_file.read()
                min_text = proc_func(text)
            output_file.write(min_text)

def generate_min_js(brand):
    new_suffix = int(time.time())
    for section, src_paths in js_files[brand].iteritems():
        min_path = _get_js_min_filename(brand, section, new_suffix)
        process_files(minify_func, src_paths, min_path)

    _fname = _get_js_suffix_filename(brand)
    with open(_fname, 'w') as f:
        f.write("%s" % new_suffix)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pack js files')
    parser.add_argument('brand', metavar='brand', choices=js_files.keys())

    args = parser.parse_args()
    if args.brand:
        generate_min_js(args.brand)
    else:
        parser.print_help()
        sys.exit(1)

