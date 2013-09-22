from common.constants import FIELD_TYPE

class FieldType:
    name = None
    field_type = None

    def __init__(self, name):
        self.name = name

class TextFieldType(FieldType):
    field_type = FIELD_TYPE.TEXT
    value = None
    accept_condition = None

    def __init__(self, name, value, accept_condition):
        FieldType.__init__(self, name)
        self.value = value
        self.accept_condition = accept_condition

    def toDict(self):
        return {"name": self.name,
                "value": self.value,
                "type": self.field_type,
                "accept": self.accept_condition,
                }

class SelectFieldType(TextFieldType):
    field_type = FIELD_TYPE.SELECT

    def __init__(self, name, value, accept_condition):
        assert type(accept_condition) is dict
        TextFieldType.__init__(self, name, value, accept_condition)

class RadioFieldType(SelectFieldType):
    field_type = FIELD_TYPE.RADIO

class AjaxFieldType(FieldType):
    field_type = FIELD_TYPE.AJAX
    value = None
    source = None
    depends = None

    def __init__(self, name, value, source, depends=""):
        FieldType.__init__(self, name)
        self.value = value
        self.source = source
        self.depends = depends

    def toDict(self):
        return {"name": self.name,
                "value": self.value,
                "type": self.field_type,
                "source": self.source,
                "depends": self.depends,
                }

class FieldSetType(FieldType):
    field_type = FIELD_TYPE.FIELDSET
    fileds_dict = None
    values = None

    def __init__(self, name, fields_dict, values):
        FieldType.__init__(self, name)
        self.fields_dict = fields_dict
        self.values = values

    def toDict(self):
        f_dict = self.fields_dict.copy()
        for f in f_dict:
            if type(f) is FieldType:
                f_dict[f] = f_dict[f].ToDict()
        return {"name": self.name,
                "type": self.field_type,
                "fields": f_dict,
                "values": self.values
                }

