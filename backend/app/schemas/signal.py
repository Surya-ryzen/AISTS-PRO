from pydantic import BaseModel


class SignalResponse(BaseModel):
    """
    Current traffic signal state.
    """

    current_green_lane: int
    state: str
    remaining_time: int
    green_time: int
    last_reason: str
