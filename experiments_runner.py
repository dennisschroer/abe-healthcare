import csv
import traceback
from cProfile import Profile
from collections import namedtuple
from multiprocessing import Condition
from multiprocessing import Process
from multiprocessing import Value
from os import makedirs
from os import path
from time import sleep
from typing import List

import psutil

from experiments.base_experiment import BaseExperiment, ExperimentCase
from experiments.file_size_experiment import FileSizeExperiment
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation
from shared.utils.measure_util import pstats_to_csv

debug = False

OUTPUT_DIRECTORY = 'data/experiments/output'


class ExperimentsRunner(object):
    def __init__(self) -> None:
        if not path.exists(OUTPUT_DIRECTORY):
            makedirs(OUTPUT_DIRECTORY)
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

    def run_experiment(self, experiment: BaseExperiment) -> None:
        i = 1
        print("=> Setting up %s, implementation=%s" % (
            experiment.__class__.__name__,
            experiment.implementation.__class__.__name__
        ))
        experiment.global_setup()
        for case in experiment.cases:
            self.run_experiment_case(experiment, case)
            i += 1

    def run_experiment_case(self, experiment: BaseExperiment, case: ExperimentCase) -> None:
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
        is_running = Value('b', False)
        p = Process(target=self.run_experiment_case_synchronously, args=(experiment, case, lock, is_running))

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
        memory_usages = list()
        process.cpu_percent()

        # Release the lock, signaling the experiment to start, and wait for the experiment to finish
        lock.notify()
        is_running.value = True
        lock.release()

        while is_running.value:
            memory_usages.append(process.memory_info())
            sleep(0.1)

        if debug:
            print("debug 6 -> gather monitoring data")

        # Gather process statistics
        self.output_cpu_usage(experiment, case, process.cpu_percent())
        self.output_memory_usages(experiment, case, memory_usages)

        # Wait for the cleanup to finish
        p.join()

        if debug:
            print("debug 8 -> process stopped")

    @staticmethod
    def run_experiment_case_synchronously(experiment: BaseExperiment, case: ExperimentCase, lock: Condition,
                                          is_running: Value) -> None:
        try:
            experiment.setup(case)

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
            is_running.value = False

            ExperimentsRunner.output_timings(experiment, case, experiment.pr)

            # Cleanup
            if debug:
                print("debug 7 -> cleanup finished")
        except BaseException as e:
            ExperimentsRunner.output_error(experiment, case, e)
        finally:
            try:
                is_running.value = False
                lock.notify()
                lock.release()
            except:
                pass

    @staticmethod
    def experiment_output_directory(experiment: BaseExperiment) -> str:
        directory = path.join(OUTPUT_DIRECTORY,
                              experiment.__class__.__name__,
                              experiment.implementation.__class__.__name__)
        if not path.exists(directory):
            makedirs(directory)
        return directory

    @staticmethod
    def output_cpu_usage(experiment: BaseExperiment, case: ExperimentCase, cpu_usage: float) -> None:
        directory = ExperimentsRunner.experiment_output_directory(experiment)
        with open(path.join(directory, '%s_cpu.txt' % case.name), 'w') as file:
            file.write(str(cpu_usage))

    @staticmethod
    def output_error(experiment: BaseExperiment, case: ExperimentCase, error: BaseException) -> None:
        directory = ExperimentsRunner.experiment_output_directory(experiment)
        with open(path.join(directory, '%s_ERROR.txt' % case.name), 'w') as file:
            traceback.print_exc(file=file)

    @staticmethod
    def output_memory_usages(experiment: BaseExperiment, case: ExperimentCase, memory_usages: List[namedtuple]) -> None:
        directory = ExperimentsRunner.experiment_output_directory(experiment)
        with open(path.join(directory, '%s_memory.csv' % case.name), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty'
            ])
            writer.writeheader()
            for row in memory_usages:
                writer.writerow(row._asdict())

    @staticmethod
    def output_timings(experiment: BaseExperiment, case: ExperimentCase, profile: Profile) -> None:
        directory = ExperimentsRunner.experiment_output_directory(experiment)
        profile.dump_stats(path.join(directory, '%s_timings.txt' % case.name))
        pstats_to_csv(path.join(directory, '%s_timings.txt' % case.name),
                      path.join(directory, '%s_timings.csv' % case.name))


if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_file_size_experiments()
