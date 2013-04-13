class LinkedinApiError(Exception):
    pass


class LinkedinAuthenticationError(LinkedinApiError):
    pass


class LinkedinUserApiError(LinkedinApiError):
    pass
