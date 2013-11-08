
class BaseCarrier:
    @classmethod
    def getRate(cls, origin_addr, dest_addr, service_type, weight):
        raise NotImplementedError

    @classmethod
    def printLable(cls, origin_addr, dest_addr, service_type, weight):
        raise NotImplementedError

class EMSCarrier():
    @classmethod
    def getRate(cls, origin_addr, dest_addr, service_type, weight):
        # TODO: calculate fee according with different case.
        return 5.0

    @classmethod
    def printLable(cls, origin_addr, dest_addr, service_type, weight):
        pass

CARRIER_CLS_SURFFIX = 'Carrier'
