from fastapi import APIRouter, Depends

from backend.app.dependencies.system import get_system
from backend.app.services.system.service import TrafficSystemService
from backend.app.schemas.statistics import StatisticsResponse
from backend.app.database.tables.user import User
from backend.app.dependencies.auth import get_current_user

router = APIRouter(
    tags=["Analytics"],
)


@router.get(
    "/statistics",
    summary="Get overall traffic statistics",
    response_model=StatisticsResponse,
)
def statistics(
    system: TrafficSystemService = Depends(get_system),
    current_user: User = Depends(get_current_user),
):

    result = system.get_latest_result()

    if result is None:

        return {"message": "No frame processed yet"}

    stats = result.statistics

    return StatisticsResponse(
        current_vehicle_count=stats.current_vehicle_count,
        total_vehicle_count=stats.total_vehicle_count,
        average_speed=stats.average_speed,
        density=stats.density,
        queue_length=stats.queue_length,
        waiting_vehicles=stats.waiting_vehicles,
        average_waiting_time=stats.average_waiting_time,
        maximum_waiting_time=stats.maximum_waiting_time,
        pcu=stats.pcu,
        traffic_flow=stats.traffic_flow,
    )
