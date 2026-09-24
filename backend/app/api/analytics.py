from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.schemas.analytics import AnalyticsResponse
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    tags=["Analytics"],
)


@router.get(
    "/analytics",
    summary="Get latest traffic analytics",
    response_model=AnalyticsResponse,
)
def analytics(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):

    result = system.get_latest_result()

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Traffic system is starting...",
        )

    statistics = result.statistics

    return AnalyticsResponse(
        current_vehicle_count=statistics.current_vehicle_count,
        total_vehicle_count=statistics.total_vehicle_count,
        average_speed=statistics.average_speed,
        density=statistics.density,
        queue_length=statistics.queue_length,
        waiting_vehicles=statistics.waiting_vehicles,
        average_waiting_time=statistics.average_waiting_time,
        maximum_waiting_time=statistics.maximum_waiting_time,
        pcu=statistics.pcu,
        traffic_flow=statistics.traffic_flow,
        vehicles_passed_last_minute=(statistics.vehicles_passed_last_minute),
    )
