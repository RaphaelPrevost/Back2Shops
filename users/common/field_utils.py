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
        assert type(accept_condition) is list
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

    def __init__(self, name, fields_dict, values, ordered_field_names=None):
        FieldType.__init__(self, name)
        self.fields_dict = fields_dict
        self.values = values
        self.ordered_field_names = ordered_field_names or self.fields_dict.keys()

    def toDict(self):
        ordered_fields = []
        for f_name in self.ordered_field_names:
            f = self.fields_dict[f_name]
            ordered_fields.append((f_name, f.toDict())
                                  if isinstance(f, FieldType) else f)
        return {"name": self.name,
                "type": self.field_type,
                "fields": ordered_fields,
                "values": self.values,
                }

