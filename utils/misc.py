import os.path


def get_delimiter(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    if ext in [".csv"]:
        return ","
    elif ext in [".tsv", ".bed"]:
        return "\t"

    return ","


def flatten(list_):
    result = []
    for item in list_:
        if isinstance(item, list) or isinstance(item, tuple):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
