from experiments.authorities_amount_experiment import AuthoritiesAmountExperiment
from experiments.base_experiment import BaseExperiment
from experiments.experiments_runner import ExperimentsRunner
from experiments.file_size_experiment import FileSizeExperiment
from experiments.policy_size_experiment import PolicySizeExperiment

if __name__ == '__main__':
    runner = ExperimentsRunner()
    runner.run_experiment(BaseExperiment())
    runner.run_experiment(FileSizeExperiment())
    runner.run_experiment(PolicySizeExperiment())
    runner.run_experiment(AuthoritiesAmountExperiment())
