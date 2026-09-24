from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.version import router as version_router
from backend.app.core.settings import settings
from backend.app.core.logging import logger
from backend.app.api.analytics import router as analytics_router
from backend.app.api.lanes import router as lanes_router
from backend.app.api.signal import router as signal_router
from backend.app.api.video import router as video_router
from backend.app.system import system
from backend.app.api.statistics import router as statistics_router
from backend.app.api.decision import router as decision_router
from backend.app.api.history import router as history_router
from backend.app.api.status import router as status_router
from backend.app.api.cameras import router as cameras_router
from backend.app.api.auth import router as auth_router
from backend.app.api.incident_detection import router as incident_detection_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)


app.include_router(health_router)
app.include_router(version_router)
app.include_router(analytics_router)
app.include_router(lanes_router)
app.include_router(signal_router)
app.include_router(video_router)
app.include_router(statistics_router)
app.include_router(decision_router)
app.include_router(history_router)
app.include_router(status_router)
app.include_router(cameras_router)
app.include_router(auth_router)
app.include_router(incident_detection_router)


@app.on_event("startup")
async def startup():

    # A local process cannot resume an in-memory worker after a restart.
    from sqlalchemy import update
    from backend.app.database.session_manager import get_db_session
    from backend.app.database.tables.forecasting import ForecastJob
    with get_db_session() as db:
        db.execute(update(ForecastJob).where(ForecastJob.status.in_(['queued','running']))
            .values(status='failed',error='Interrupted by backend restart; resubmit the training job.'))
    system.start()

    logger.info("Backend Started")


@app.on_event("shutdown")
async def shutdown():

    system.stop()

    logger.info("Backend Stopped")

from backend.app.api.road_setup import router as road_setup_router
app.include_router(road_setup_router)




from backend.app.api.week10 import router as week10_router
app.include_router(week10_router)

from backend.app.api.predictions import router as predictions_router
app.include_router(predictions_router)

from backend.app.api.forecasting import router as forecasting_router
app.include_router(forecasting_router)
