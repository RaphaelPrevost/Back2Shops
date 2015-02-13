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


import ujson

class BaseActor(object):
    attrs_map = {}
    def __init__(self, data=None, xml_data=None):
        if xml_data:
            self.data = ujson.loads(xml_data)
        else:
            self.data = data

    def __getattr__(self, item, default=None):
        assert item in self.attrs_map
        item_name = self.attrs_map[item]
        return self.data.get(item_name)

    def exist(self, attr):
        key = self.attrs_map.get(attr)
        if key is None:
            return False
        return key in self.data

def _list_actor_to_dict(list_actor):
    list_prop = []
    for item in list_actor:
        if isinstance(item, BaseActor):
            list_prop.append(actor_to_dict(item))
        elif isinstance(item, list):
            list_prop.append(_list_actor_to_dict(item))
        elif isinstance(item, dict):
            list_prop.append(_dict_actor_to_dict(item))
        else:
            list_prop.append(item)
    return list_prop

def _dict_actor_to_dict(dict_actor):
    new_d = {}
    for key, value in dict_actor.iteritems():
        if isinstance(value, list):
            new_d[key] = _list_actor_to_dict(value)
        elif isinstance(value, dict):
            new_d[key] = _dict_actor_to_dict(value)
        elif isinstance(value, BaseActor):
            new_d[key] = actor_to_dict(value)
        else:
            new_d[key] = value
    return new_d

def actor_to_dict(actor):
    props = []
    for prop, _ in actor.__class__.__dict__.iteritems():
        if prop.startswith('__'):
            continue

        if isinstance(getattr(type(actor), prop), property):
            props.append(prop)

    d = {}
    for prop in props:
        value = getattr(actor, prop, None)
        if isinstance(value, BaseActor):
            d[prop] = actor_to_dict(value)
        elif isinstance(value, list):
            d[prop] = _list_actor_to_dict(value)
        elif isinstance(value, dict):
            d[prop] = _dict_actor_to_dict(value)
        else:
            d[prop] = value

    for prop in actor.attrs_map.keys():
        d[prop] = getattr(actor, prop, None)

    return d

def as_list(data):
    if not data:
        return []
    if not isinstance(data, list):
        return [data]
    return data

