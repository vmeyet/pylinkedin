class LinkedinApiError(Exception):
    pass


class LinkedinAuthenticationError(LinkedinApiError):
    pass


class LinkedinUserApiError(LinkedinApiError):
    pass


class UnavailableMethodForEndpointError(LinkedinUserApiError):

    def __init__(self, method_name, endpoint):
        self.method_name = method_name
        self.endpoint = endpoint

    def __str__(self):
        return 'Cannot use method "%s" on the endpoint %s' % (
            self.method_name, self.endpoint
        )
