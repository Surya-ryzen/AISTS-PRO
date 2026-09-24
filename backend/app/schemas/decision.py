from pydantic import BaseModel


class DecisionResponse(BaseModel):
    """
    Latest AI traffic decision.
    """

    selected_lane: int
    green_time: int
    reason: str
