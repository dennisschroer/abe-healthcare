import cProfile
from pstats import Stats


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

    def run(self, input):
        raise NotImplementedError()

    def after_run(self):
        stats = Stats(self.pr)
        stats.strip_dirs().sort_stats('cumtime').print_stats(
            '(user|authority|insurance|storage|RSA)')
        self.pr.clear()
