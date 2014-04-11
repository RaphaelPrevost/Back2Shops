
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

    # Payment Form Error
    PMF_INVALID_REQ = (
        101, "Invalid Payment Form Request"
    )

