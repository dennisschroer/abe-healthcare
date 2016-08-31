from typing import Dict, Any


class ExperimentCase(object):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments