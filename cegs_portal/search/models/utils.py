from psycopg2.extras import NumericRange


class ChromosomeLocation:
    def __init__(self, chromo, start, end=None):
        self.chromo = chromo
        if end is None:
            self.range = NumericRange(int(start), int(start), bounds="[]")
        else:
            self.range = NumericRange(int(start), int(end))
