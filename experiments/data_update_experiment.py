import os
from typing import List

from os.path import join

from os import path

from experiments.base_experiment import BaseExperiment
from experiments.enum.abe_step import ABEStep
from experiments.runner.experiment_case import ExperimentCase
from experiments.runner.experiment_output import OUTPUT_DETAILED


class DataUpdateExperiment(BaseExperiment):
    run_descriptions = {
        'setup_authsetup': 'once',
        'register_keygen': 'once',
        'encrypt': 'once',
        'update_keys': 'once',
        'decrypt': 'never'
    }
    generated_file_amount = 2

    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        super().__init__(cases)

    def setup(self) -> None:
        # Overrided te not clear insurance storage before each run
        if OUTPUT_DETAILED and not path.exists(self.output.experiment_case_iteration_results_directory()):
            os.makedirs(self.output.experiment_case_iteration_results_directory())
        self.reset_user_clients()

    def setup_implementation_directories(self) -> None:
        # Overrided to clear insurance storage for each implementation
        super().setup_implementation_directories()
        self.clear_insurance_storage()

    @property
    def update_file_name(self) -> str:
        """File name of the file to encrypt. Is set during the experiment"""
        return join(self.get_experiment_input_path(), '%i-1' % self.encrypted_file_size)

    def run_current_state(self):
        self.log_current_state()
        # noinspection PyBroadException
        try:
            self.setup()
            self.start_measurements()

            self.run_step(ABEStep.data_update, self._run_data_update)

            self.stop_measurements()
            self.tear_down()
            self.finish_measurements()
        except KeyboardInterrupt:
            raise
        except:
            self.output.output_error()

    def _run_data_update(self):
        with open(self.update_file_name, 'rb') as update_file:
            self.user_clients[1].update_file(self.location, update_file.read())
