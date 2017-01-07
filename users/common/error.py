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

    # Order error
    OUT_OF_STOCK = (
        100, "OUT_OF_STOCK_%s"
    )

    COUPON_ERR_GIFTS_NEED_SELECT_GIFTS = (
        103, "COUPON_ERR_GIFTS_NEED_SELECT_GIFTS"
    )
    COUPON_ERR_GIFTS_EXCEED_MAX_SELECTION = (
        104, "COUPON_ERR_GIFTS_EXCEED_MAX_SELECTION"
    )
    COUPON_ERR_GIFTS_INVALID_ITEM = (
        105, "COUPON_ERR_GIFTS_INVALID_ITEM"
    )
    COUPON_ERR_GIFTS_INVALID_QUANTITY = (
        106, "COUPON_ERR_GIFTS_INVALID_QUANTITY"
    )


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

    # user model error
    UR_NO_PHONE = (
        142, 'user\'s phone not exist:'
             'user: %s, selected phone: %s'
    )

    # shipping fee error
    SF_MISS_PARAMS = (
        151, "Neither shipment nor sale provided in rquest"
    )

    # shipment request error
    ERR_EPERM = (
        161, "ERR_EPERM"  # content does not belong to the shopkeeper or
                          # the shopkeeper tries to delete a
                          # SHIPMENT_DELIVER shipment
    )

    ERR_ENOENT = (
        162, "ERR_ENOENT" # the order or shipment does not exist
    )

    ERR_EINVAL = (
        163, "ERR_EINVAL" # the content is incorrect (either ID
                          # or conflicting shipment)
                          # or the shipping fees are incorrect
    )

    ERR_ESTATUS = (
        164, "ERR_ESTATUS" # the status flag set is incorrect
    )

    ERR_ETIME = (
        165, "ERR_ETIME" # the date is incorrect.
    )

    ERR_EREQ = (
        166, "ERR_EREQ" # the request is invalid, e.g. miss params...
    )

    ERR_ECONTENT = (
        167, "ERR_ECONTENT" # fields missed for content param
                            # or order item doesn't exist
                            # or order items' brand not same.
    )

    # payment errors
    PM_ERR_INVALID_REQ = (
        170, "Invalid Request"
    )

    # paypal errors
    PP_ERR_RECEIVER_EMAIL = (
        180, 'Invalid Receiver Email'
    )
    PP_ERR_NO_TRANS = (
        181, 'Processed transaction not exist'
    )
    PP_ERR_MC_GROSS = (
        182, 'Processed mc_gross is not as expected'
    )

    # Finance paypal verified error
    PP_FIN_HANDLED_ERR = (
        183, 'Paypal failed to handled in finance server'
    )
    # paybox errors
    PB_ERR_WRONG_AUTH = (
        190, 'Processed transaction has wrong authorization number'
    )
    PB_ERR_REJECTED_TRANS = (
        191, 'Processed transaction is rejected'
    )
    PB_ERR_NO_TRANS = (
        192, 'Processed transaction not exist'
    )
    PB_ERR_WRONG_AMOUNT = (
        193, 'Processed amount is not as expected'
    )
    PB_ERR_WRONG_ORDER = (
        194, 'Processed order is not as expected'
    )
    # Finance paybox verified error
    PB_FIN_HANDLED_ERR = (
        195, 'Paybox failed to handled in finance server'
    )


error_code_mapping = {}
for attr_name in dir(ErrorCode):
    if attr_name.startswith('__'):
        continue
    error = getattr(ErrorCode, attr_name)
    error_code_mapping[error[0]] = error[1]

