from enum import Enum

class RESP_RESULT(Enum):
    S = "SUCCESS"
    F = "FAILURE"

class HASH_ALGORITHM(Enum):
    WHIRLPOOL = 1

HASH_ALGORITHM_NAME = {
    HASH_ALGORITHM.WHIRLPOOL: "whirlpool",
}

