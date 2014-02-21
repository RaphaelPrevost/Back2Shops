
class ServerError(Exception):
    pass

class NotExistError(Exception):
    pass

class UserError(Exception):
    def __init__(self, code, desc, *args, **kwargs):
        super(UserError, self).__init__(*args, **kwargs)
        self.code = code
        self.desc = desc

    def __str__(self):
        return ' - '.join([str(self.code), str(self.desc)])

class ErrorCode:

    # Sale shipping fee error
    SSF_MISS_PARAM = (
        101, "SSF Invalid Request: "
             "You must provide id_weight_type "
             "and id_shop if you want to get shipping "
             "fee for sale %s"
    )

    SSF_NOT_SUPPORT_SERVICE = (
        102, "SSF invalid shipping fee request:"
             "sale %s doesn't support service "
             "%s - %s"
    )

    # Shipment shipping fee error
    SPSF_NOT_SUPPORT_SERVICE = (
        111, "SPSF invalid shipping fee request:"
             "shipment %s doesn't support service "
             "%s - %s"
    )

    # Pub shipment list error
    PSPL_PRIORITY_ERROR = (
        121, "PSPL You have no priority to this order: "
             "(order %s - user %s)"
    )

    PSPL_MISS_PARAMS = (
        122, "PSPL Invalid Request: no sale id or "
             "shipment id in request"
    )

    # Shipping conf error
    SP_MISS_PARAMS = (
        131, "shipping conf request miss param: %s"
    )

    SP_PRIORITY_ERROR = (
        132, "SP request error: "
             "you(%s) have no priority to operate this "
             "shipment: %s"
    )

    SP_INVALID_SERVICE = (
        133, "SP request error:"
             "specify shipment(%s) not support selected "
             "service: %s - %s"
    )

    # user model error
    UR_NO_ADDR = (
        141, 'user\'s address not exist:'
             'user: %s, destination address: %s'
    )

    # shipping fee error
    SF_MISS_PARAMS = (
        151, "Neither shipment nor sale provided in rquest"
    )