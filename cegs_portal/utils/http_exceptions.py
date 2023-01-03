class Http303(Exception):
    def __init__(self, message: str, location) -> None:
        super().__init__(message)
        self.location = location


class Http400(Exception):
    """Bad Request"""


class Http500(Exception):
    """Internal Server Error"""
