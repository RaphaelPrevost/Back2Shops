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

class USERS_ROLE(CustomEnum):
    ADMIN = 1       # brand administrator
    MANAGER = 2     # shopkeeper
    OPERATOR = 3    # operator

