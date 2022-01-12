import os.path


def get_delimiter(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    if ext == ".csv":
        return ","
    elif ext == ".tsv":
        return "\t"

    return ","
