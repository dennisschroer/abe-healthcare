from enum import Enum


class MeasurementType(Enum):
    timings = 1
    storage_and_network = 2
    memory = 3
    cpu = 4
