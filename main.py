from experiments.authorities_amount_experiment import AuthoritiesAmountExperiment
from experiments.base_experiment import BaseExperiment
from experiments.data_update_experiment import DataUpdateExperiment
from experiments.disjunctive_policy_size_experiment import DisjunctivePolicySizeExperiment
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment
from experiments.runner.experiments_runner import ExperimentsRunner
from experiments.user_key_size_experiment import UserKeySizeExperiment

IS_MOBILE = False

if __name__ == '__main__':
    runner = ExperimentsRunner()
    base_experiment = BaseExperiment()
    policy_size_experiment = PolicySizeExperiment()
    disjunctive_policy_size_experiment = DisjunctivePolicySizeExperiment()
    user_key_size_experiment = UserKeySizeExperiment()
    authorities_amount_experiment = AuthoritiesAmountExperiment()
    file_size_experiment = FileSizeExperiment()
    data_update_experiment = DataUpdateExperiment()

    if IS_MOBILE:
        base_experiment.run_descriptions = {
            'setup_authsetup': 'once',
            'register_keygen': 'once'
        }
        # Storage and network are skipped, as they are just the same as on notebook
        base_experiment.measurement_types_once = []

    runner.run_experiment(base_experiment)
    runner.run_experiment(policy_size_experiment)
    runner.run_experiment(disjunctive_policy_size_experiment)
    runner.run_experiment(user_key_size_experiment)
    runner.run_experiment(authorities_amount_experiment)
    runner.run_experiment(file_size_experiment)
    runner.run_experiment(data_update_experiment)
