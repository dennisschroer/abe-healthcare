import cProfile
from pstats import Stats

from os import path

PROFILE_DATA_DIRECTORY = 'data/profile'


class BaseExperiment(object):
    def __init__(self):
        self.pr = cProfile.Profile()
        self.cases = list()

    def setup(self):
        raise NotImplementedError()

    def start_measurements(self):
        self.pr.enable()

    def stop_measurements(self):
        self.pr.disable()

    def run(self, case):
        raise NotImplementedError()

    def after_run(self, case):
        stats = Stats(self.pr)
        self.pr.dump_stats(path.join(PROFILE_DATA_DIRECTORY, '%s-%s.txt' % (self.__class__.__name__, case['name'])))
        stats.strip_dirs().sort_stats('cumtime').print_stats(
            '(user|authority|insurance|storage|RSA)')
        self.pr.clear()
