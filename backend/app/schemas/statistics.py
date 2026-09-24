from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    """
    Overall traffic analytics response.
    """

    current_vehicle_count: int
    total_vehicle_count: int
    average_speed: float
    density: float
    queue_length: int
    waiting_vehicles: int
    average_waiting_time: float
    maximum_waiting_time: float
    pcu: float
    traffic_flow: float
