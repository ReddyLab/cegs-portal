import os.path


def get_delimiter(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    if ext in [".csv"]:
        return ","
    elif ext in [".tsv", ".bed"]:
        return "\t"

    return ","
