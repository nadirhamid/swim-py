
class SwimException(Exception):
    pass

class SwimOptionException(SwimException):
    pass

class SwimPingFailedException(SwimException):
    pass

class SwimPingRequestFailedException(SwimException):
    pass
