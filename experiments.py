from experiments.file_size_experiment import FileSizeExperiment
from shared.implementations.rw15_implementation import RW15Implementation

if __name__ == '__main__':
    experiment = FileSizeExperiment(RW15Implementation())
    print("=> Running %s" % experiment.__class__.__name__)
    print("Setup...")
    experiment.setup()
    print("Running...")
    experiment.run()
    print("Outputting results...")

    print("Done")
