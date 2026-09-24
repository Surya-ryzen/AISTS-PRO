from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
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
    vehicles_passed_last_minute: int
