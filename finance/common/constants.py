from enum import Enum

class CustomEnum(Enum):
    @classmethod
    def toDict(self):
        result = {}
        for k, v in self.__dict__.iteritems():
            if k.startswith('__'):
                continue
            result[k] = v
        return result

class RESP_RESULT(CustomEnum):
    S = "SUCCESS"
    F = "FAILURE"

class CUR_CODE(CustomEnum):
    EUR = 978
    USD = 840
