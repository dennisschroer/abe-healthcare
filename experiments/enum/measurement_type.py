from enum import Enum


class MeasurementType(Enum):
    timings = 1
    storage = 2
    network = 3
    memory = 4
    cpu = 5