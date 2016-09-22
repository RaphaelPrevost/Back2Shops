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
    show = None

    def __init__(self, name, value, accept_condition, show=None):
        FieldType.__init__(self, name)
        self.value = value
        self.accept_condition = accept_condition
        self.show = show

    def toDict(self):
        d = {
            "name": self.name,
            "value": self.value,
            "type": self.field_type,
            "accept": self.accept_condition,
        }
        if self.show:
            d['show'] = self.show
        return d

class SelectFieldType(TextFieldType):
    field_type = FIELD_TYPE.SELECT

    def __init__(self, name, value, accept_condition, show=None):
        assert type(accept_condition) is list
        TextFieldType.__init__(self, name, value, accept_condition,
                               show=show)

class RadioFieldType(SelectFieldType):
    field_type = FIELD_TYPE.RADIO

class CheckboxFieldType(TextFieldType):
    field_type = FIELD_TYPE.CHECKBOX

    def __init__(self, name, value, accept_condition='', show=''):
        value = 'checked' if value else ''
        TextFieldType.__init__(self, name, value, accept_condition,
                               show=show)

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

