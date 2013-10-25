import ujson

class BaseActor(object):
    attrs_map = {}
    def __init__(self, data=None, xml_data=None):
        if xml_data:
            self.data = ujson.loads(xml_data)
        else:
            self.data = data

    def __getattr__(self, item):
        assert item in self.attrs_map
        item_name = self.attrs_map[item]
        return self.data.get(item_name)
