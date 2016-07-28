import os

from shared.utils.random_file_generator import RandomFileGenerator


class FileSizeExperiment(object):
    data_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/file_size_experiment')

    def __init__(self, sizes=None):
        if sizes is None:
            sizes= [1, 2 ** 10, 2 ** 20, 2 ** 30]
        self.sizes = sizes

    def setup(self):
        file_generator = RandomFileGenerator()
        for file_size in self.sizes:
            file_generator.generate(file_size, 2, self.data_location, skip_if_exists=True)

    def run(self):
        pass


if __name__ == '__main__':
    experiment = FileSizeExperiment()
    experiment.setup()
    experiment.run()
