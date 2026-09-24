from pydantic import BaseModel


class LaneResponse(BaseModel):
    """
    Lane-wise traffic analytics response.
    """

    lane_id: int
    vehicle_count: int
    average_speed: float
    density: float
    queue_length: int
    traffic_flow: float
