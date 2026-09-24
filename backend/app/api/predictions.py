from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from backend.app.dependencies.auth import get_current_user, get_db
from backend.app.services.prediction.service import forecast

router = APIRouter(prefix='/predictions', tags=['Forecasting'])


@router.get('/lanes/{lane_id}', summary='Latest source-scoped one-minute lane forecast')
def lane_forecast(lane_id: int = Path(ge=1,le=8), user=Depends(get_current_user),
                  db: Session = Depends(get_db)):
    try:
        from sqlalchemy import select
        from backend.app.database.tables.forecasting import ForecastStream
        from backend.app.services.prediction.runtime import forecast_stream
        stream=db.scalar(select(ForecastStream).where(ForecastStream.data_kind=='live')
            .order_by(ForecastStream.created_at.desc()).limit(1))
        if stream is None:
            raise ValueError('No source-scoped live stream. Use /forecasting/streams for recorded or imported data.')
        return forecast_stream(db,stream.id,lane_id,1)
    except ValueError as exc:
        raise HTTPException(503,str(exc)) from exc
