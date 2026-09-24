"""
Analytics execution pipeline.

Each calculator updates the shared
TrafficStatistics object.
"""

from backend.app.services.analytics.calculators.vehicle_counter import VehicleCounter
from backend.app.services.analytics.calculators.average_speed import (
    AverageSpeedCalculator,
)
from backend.app.services.analytics.calculators.traffic_density import (
    TrafficDensityCalculator,
)
from backend.app.services.analytics.calculators.queue_length import (
    QueueLengthCalculator,
)
from backend.app.services.analytics.calculators.waiting_time import (
    WaitingTimeCalculator,
)
from backend.app.services.analytics.calculators.pcu import PCUCalculator
from backend.app.services.analytics.calculators.traffic_flow import (
    TrafficFlowCalculator,
)

PIPELINE = [
    VehicleCounter(),
    AverageSpeedCalculator(),
    TrafficDensityCalculator(),
    QueueLengthCalculator(),
    WaitingTimeCalculator(),
    PCUCalculator(),
    TrafficFlowCalculator(),
]
