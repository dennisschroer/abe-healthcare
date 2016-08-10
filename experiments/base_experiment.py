import cProfile
from os import path, makedirs
from pstats import Stats
from typing import List, Dict, Any

from shared.implementations.base_implementation import BaseImplementation

PROFILE_DATA_DIRECTORY = 'data/profile'


class ExperimentCase(object):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments


class BaseExperiment(object):
    def __init__(self, implementation: BaseImplementation) -> None:
        self.pr = cProfile.Profile()
        self.implementation = implementation
        self.cases = list()  # type: List[ExperimentCase]

        if not path.exists(PROFILE_DATA_DIRECTORY):
            makedirs(PROFILE_DATA_DIRECTORY)

    def setup(self):
        raise NotImplementedError()

    def start_measurements(self):
        self.pr.enable()

    def stop_measurements(self):
        self.pr.disable()

    def run(self, case: ExperimentCase):
        raise NotImplementedError()

    def after_run(self, case: ExperimentCase):
        stats = Stats(self.pr)
        self.pr.dump_stats(path.join(PROFILE_DATA_DIRECTORY, '%s-%s-%s.txt' % (
        self.__class__.__name__, self.implementation.__class__.__name__, case.name)))
        stats.strip_dirs().sort_stats('cumtime').print_stats(
            '(user|authority|insurance|storage|RSA)')
        self.pr.clear()
