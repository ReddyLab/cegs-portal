from enum import Enum, auto
from typing import Optional

from psycopg2.extras import NumericRange


class QueryToken(Enum):
    LOCATION = auto()
    ENSEMBL_ID = auto()
    ACCESSION_ID = auto()

    def associate(self, value: str) -> tuple["QueryToken", str]:
        return (self, value)


class ChromosomeLocation:
    def __init__(self, chromo: str, start: str, end: Optional[str] = None):
        self.chromo = chromo
        if end is None:
            self.range = NumericRange(int(start), int(start), bounds="[]")
        else:
            self.range = NumericRange(int(start), int(end))

    def __str__(self) -> str:
        return f"{self.chromo}: {self.range.lower}-{self.range.upper}"

    def __repr__(self) -> str:
        return self.__str__()
