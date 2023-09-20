from enum import Enum

JSON_MIME = "application/json"


class UserType(Enum):
    ANONYMOUS = 1
    ADMIN = 2
    LOGGED_IN = 3
