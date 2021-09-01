from enum import Enum, auto

from psycopg2.extras import NumericRange


class QueryToken(Enum):
    LOCATION = auto()
    ENSEMBL_ID = auto()

    def associate(self, value):
        return (self, value)


class ChromosomeLocation:
    def __init__(self, chromo, start, end=None):
        self.chromo = chromo
        if end is None:
            self.range = NumericRange(int(start), int(start), bounds="[]")
        else:
            self.range = NumericRange(int(start), int(end))
