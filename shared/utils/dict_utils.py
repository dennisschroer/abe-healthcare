from types import FunctionType
from typing import Dict, Any


def merge_dicts(*dict_args: dict) -> dict:
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = dict()  # type: dict
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def dict_equals_except_functions(a: Dict[str, Any], b: Dict[str, Any]):
    if a.keys() != b.keys():
        return False
    for key in a.keys():
        if not isinstance(a[key], FunctionType) or not isinstance(b[key], FunctionType):
            if a[key] != b[key]:
                return False
    return True
