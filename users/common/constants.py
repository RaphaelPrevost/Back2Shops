from B2SProtocol.constants import CustomEnum

class FIELD_TYPE(CustomEnum):
    TEXT = "text"
    SELECT = "select"
    RADIO = "radio"
    FIELDSET = "fieldset"
    AJAX = "ajax"

class GENDER(CustomEnum):
    Male = "M"
    Female = "F"
    Other = "O"

class ADDR_TYPE(CustomEnum):
    Shipping = 0
    Billing = 1
    Both = 2

class HASH_ALGORITHM(CustomEnum):
    WHIRLPOOL = 1
    SHA256 = 2


class RETURN_STATUS(CustomEnum):
    RETURN_ELIGIBLE = 1
    RETURN_REJECTED = 2 #1 << 1
    RETURN_RECEIVED = 4 #1 << 2
    RETURN_EXAMINED = 8 #1 << 3
    RETURN_ACCEPTED = 16 #1 << 4
    RETURN_REJECTED = 32 #1 << 5
    RETURN_PROPOSAL = 64 #1 << 6
    RETURN_REFUNDED = 128 #1 << 7
    RETURN_REJECTED_FRAUD = 256 #1 << 8
    RETURN_REJECTED_INVAL = 512 #1 << 9
    RETURN_PROPOSAL_ACCEPT = 1024 #1 << 10
    RETURN_PROPOSAL_REJECT = 2048 #1 << 11

HASH_ALGORITHM_NAME = {
    HASH_ALGORITHM.WHIRLPOOL: "whirlpool",
    HASH_ALGORITHM.SHA256: "sha256",
}

PAYPAL_VERIFIED = 'VERIFIED'
PAYPAL_INVALID = 'INVALID'

class PAYMENT_TYPES(CustomEnum):
    PAYPAL = 'Paypal'
    PAYBOX = 'Paybox'


RESET_PASSWORD_REDIS_KEY = 'RESET_PWD:%s'

