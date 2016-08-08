from experiments.file_size_experiment import FileSizeExperiment
from shared.implementations.rw15_implementation import RW15Implementation

if __name__ == '__main__':
    experiment = FileSizeExperiment(RW15Implementation())
    print("=> Running %s" % experiment.__class__.__name__)
    print("Setup...")
    experiment.setup()
    print("Running...")
    i = 1
    for case in experiment.cases:
        print("%d/%d" % (i, len(experiment.cases)))
        experiment.start_measurements()
        experiment.run(case)
        experiment.stop_measurements()
        experiment.after_run()
        i += 1
    print("Done")
