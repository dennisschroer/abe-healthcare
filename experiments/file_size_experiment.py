from os.path import join
from typing import List, Dict, Any

from client.user_client import UserClient
from experiments.base_experiment import BaseExperiment, ExperimentCase
from service.central_authority import CentralAuthority
from service.insurance_service import InsuranceService
from shared.connection.base_connection import BaseConnection
from shared.connection.user_insurance_connection import UserInsuranceConnection
from shared.implementations.base_implementation import BaseImplementation
from shared.model.user import User
from shared.serializer.pickle_serializer import PickleSerializer
from shared.utils.random_file_generator import RandomFileGenerator


class FileSizeExperiment(BaseExperiment):
    def __init__(self, cases: List[ExperimentCase] = None) -> None:
        super().__init__()
        if cases is None:
            cases = list(map(lambda size: ExperimentCase(size, {'file_size': size}), [1, 2 ** 10, 2 ** 20, 2 ** 30]))
        self.cases = cases

        self.file_sizes = list(map(lambda case: case.arguments['file_size'], self.cases))

    def global_setup(self) -> None:
        """
        Setup all implementation and case independent things for this experiment, like generating random input files.
        This method is only called once for each experiment, namely at the very start.
        """
        file_generator = RandomFileGenerator()
        input_path = self.get_experiment_input_path()
        for file_size in self.file_sizes:
            file_generator.generate(file_size, 1, input_path, skip_if_exists=True, verbose=True)

    def setup(self, implementation: BaseImplementation, case: ExperimentCase):
        super().setup(implementation, case)
        input_path = self.get_experiment_input_path()
        self.file_name = join(input_path, '%i-0' % case.arguments['file_size'])
