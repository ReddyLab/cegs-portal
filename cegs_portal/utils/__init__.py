def truthy_to_bool(value):
    if isinstance(value, bool):
        return value

    if value == "0" or value == "false" or value == "False":
        return False
    else:
        return True
