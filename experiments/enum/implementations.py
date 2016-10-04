from typing import List

from shared.implementations.base_implementation import BaseImplementation
from shared.implementations.dacmacs13_implementation import DACMACS13Implementation
from shared.implementations.rd13_implementation import RD13Implementation
from shared.implementations.rw15_implementation import RW15Implementation
from shared.implementations.taac12_implementation import TAAC12Implementation

implementations = [
    DACMACS13Implementation(),
    RD13Implementation(),
    RW15Implementation(),
    TAAC12Implementation()
]  # type: List[BaseImplementation]
