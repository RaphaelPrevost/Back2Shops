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
    for key, value in dict_actor:
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
        value = getattr(actor, prop)
        if isinstance(value, BaseActor):
            d[prop] = actor_to_dict(value)
        elif isinstance(value, list):
            d[prop] = _list_actor_to_dict(value)
        elif isinstance(value, dict):
            d[prop] = _dict_actor_to_dict(value)
        else:
            d[prop] = value

    for prop in actor.attrs_map.keys():
        d[prop] = getattr(actor, prop)

    return d

