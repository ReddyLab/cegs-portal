def integerRangeDict(int_range):
    return {
        "start": int_range.lower,
        "end": int_range.upper - 1,  # The db upper value is open but we want to return a closed value.
    }
