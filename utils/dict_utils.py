def merge_dicts(*dict_args: dict) -> dict:
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = dict()  # type: dict
    for dictionary in dict_args:
        result.update(dictionary)
    return result
