class UsersServerError(Exception):
    pass

class InvalidRequestError(Exception):
    pass

class ParamsValidCheckError(InvalidRequestError):
    pass
