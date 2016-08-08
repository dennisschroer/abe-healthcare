class BaseExperiment(object):
    def setup(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
