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

#TODO move to B2SProtocol later
class FRT_ROUTE_ROLE(CustomEnum):
    PRDT_LIST = "PRDT_LIST"
    PRDT_INFO = "PRDT_INFO"
