from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrafficHistoryResponse(BaseModel):
    id: int
    timestamp: datetime

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

    model_config = ConfigDict(from_attributes=True)


class LaneHistoryResponse(BaseModel):
    id: int
    timestamp: datetime

    lane_id: int
    vehicle_count: int
    average_speed: float
    density: float
    queue_length: int
    traffic_flow: float

    model_config = ConfigDict(from_attributes=True)


class SignalHistoryResponse(BaseModel):
    id: int
    timestamp: datetime

    selected_lane: int
    green_time: int
    reason: str

    model_config = ConfigDict(from_attributes=True)
