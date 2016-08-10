from multiprocessing import Condition
from multiprocessing import Process

import psutil

from experiments.base_experiment import BaseExperiment, ExperimentCase
from experiments.file_size_experiment import FileSizeExperiment
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation

debug = False


class ExperimentRunner(object):
    def __init__(self):
        self.implementations = [
            RW15Implementation(),
            DACMACS13Implementation(),
            RD13Implementation(),
            TAAC12Implementation()
        ]

    def run_file_size_experiments(self):
        for implementation in self.implementations:
            experiment = FileSizeExperiment(implementation)
            self.run_experiment(experiment)

    def run_experiment(self, experiment):
        i = 1
        for case in experiment.cases:
            self.run_experiment_case(experiment, case)
            i += 1

    def run_experiment_case(self, experiment: BaseExperiment, case: ExperimentCase):
        print("=> Running %s, implementation=%s (%d/%d), case=%s (%d/%d)" % (
            experiment.__class__.__name__,
            experiment.implementation.__class__.__name__,
            self.implementations.index(experiment.implementation) + 1,
            len(self.implementations),
            case.name,
            experiment.cases.index(case) + 1,
            len(experiment.cases)
        ))

        # Create a lock
        lock = Condition()
        lock.acquire()

        # Create a separate process
        p = Process(target=self.run_experiment_case_synchronously, args=(experiment, case, lock))

        if debug:
            print("debug 1 -> start process")

        # Start the process
        p.start()

        # Wait until the setup of the experiment is finished
        lock.wait()

        if debug:
            print("debug 3 -> start monitoring")

        # Setup is finished, start monitoring
        process = psutil.Process(p.pid)
        process.cpu_percent()

        # Release the lock, signaling the experiment to start, and wait for the experiment to finish
        lock.notify()
        lock.wait()

        if debug:
            print("debug 6 -> gather monitoring data")

        # Gather process statistics
        print(process.cpu_percent())

        # Wait for the cleanup to finish
        p.join()

        if debug:
            print("debug 8 -> process stopped")

    @staticmethod
    def run_experiment_case_synchronously(experiment: BaseExperiment, case: ExperimentCase, lock: Condition):
        experiment.setup()

        # We are done, let the main process setup monitoring
        lock.acquire()
        if debug:
            print("debug 2 -> experiment setup finished")
        lock.notify()
        lock.wait()
        if debug:
            print("debug 4 -> start experiment")

        # And off we go
        experiment.start_measurements()
        experiment.run(case)
        experiment.stop_measurements()

        # We are done, notify the main process to stop monitoring
        if debug:
            print("debug 5 -> stop experiment")
        lock.notify()
        lock.release()

        # Cleanup
        experiment.after_run(case)
        if debug:
            print("debug 7 -> cleanup finished")


if __name__ == '__main__':
    runner = ExperimentRunner()
    runner.run_file_size_experiments()
