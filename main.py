from experiments.authorities_amount_experiment import AuthoritiesAmountExperiment
from experiments.base_experiment import BaseExperiment
from experiments.experiments_runner import ExperimentsRunner
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment

IS_MOBILE = False

if __name__ == '__main__':
    runner = ExperimentsRunner()
    base_experiment = BaseExperiment()
    policy_size_experiment = PolicySizeExperiment()
    authorities_amount_experiment = AuthoritiesAmountExperiment()
    file_size_experiment = FileSizeExperiment()

    if IS_MOBILE:
        base_experiment.run_descriptions = {
            'setup_authsetup': 'once',
            'register_keygen': 'once'
        }

    runner.run_experiment(base_experiment)
    runner.run_experiment(policy_size_experiment)
    runner.run_experiment(authorities_amount_experiment)
    runner.run_experiment(file_size_experiment)
