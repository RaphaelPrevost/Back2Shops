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

class TARGET_MARKET_TYPES(CustomEnum):
    GLOBAL = 'N'
    LOCAL = 'L'

class ORDER_STATUS(CustomEnum):
    PENDING = 1
    AWAITING_PAYMENT = 2
    AWAITING_SHIPPING = 3
    COMPLETED = 4

# response
SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
