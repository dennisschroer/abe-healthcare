from experiments.file_size_experiment import FileSizeExperiment
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation

if __name__ == '__main__':
    implementations = [
        RW15Implementation(),
        DACMACS13Implementation(),
        RD13Implementation(),
        TAAC12Implementation()
    ]

    for implementation in implementations:
        experiment = FileSizeExperiment(implementation)
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
            experiment.after_run(case)
            i += 1
        print("Done")
