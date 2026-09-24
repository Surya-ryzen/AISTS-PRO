import hashlib
import json
import uuid
from datetime import datetime,timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from backend.app.database.tables.forecasting import ForecastStream,ForecastSample,ForecastModel,ForecastJob,ForecastResult
from backend.app.database.tables.week10 import now
from backend.app.database.session import SessionLocal
from .model import train,infer


def run_job(job_id, factory=SessionLocal):
    with factory() as db:
        job=db.get(ForecastJob,job_id)
        if job is None or job.status!='queued':return
        changed=db.execute(update(ForecastJob).where(ForecastJob.id==job_id,ForecastJob.status=='queued')
            .values(status='running',updated_at=now()))
        db.commit()
        if not changed.rowcount:return
        try:
            rows=list(db.scalars(select(ForecastSample).where(ForecastSample.stream_id==job.stream_id,
                ForecastSample.lane_id==job.lane_id).order_by(ForecastSample.minute.desc()).limit(10000)))
            rows.reverse()
            artifact=train(rows,job.horizon)
            model=ForecastModel(id=uuid.uuid4().hex,stream_id=job.stream_id,lane_id=job.lane_id,
                horizon=job.horizon,trained_through=rows[-1].minute,artifact_json=json.dumps(artifact,allow_nan=False))
            db.add(model);job.model_id=model.id;job.status='succeeded';job.updated_at=now();db.commit()
        except Exception as exc:
            db.rollback();job=db.get(ForecastJob,job_id);job.status='failed';job.updated_at=now()
            job.error=str(exc)[:500] if isinstance(exc,ValueError) else 'Training failed; check backend logs.'
            db.commit()
            if not isinstance(exc,ValueError):
                import logging
                logging.getLogger(__name__).exception('Forecast training failed')


def forecast_stream(db,stream_id,lane_id,horizon,require_fresh=True):
    stream=db.get(ForecastStream,stream_id)
    if stream is None:raise LookupError('Forecast stream not found.')
    rows=list(db.scalars(select(ForecastSample).where(ForecastSample.stream_id==stream_id,
        ForecastSample.lane_id==lane_id).order_by(ForecastSample.minute.desc()).limit(6)))
    rows.reverse()
    if len(rows)<6:raise ValueError('Need six completed minute samples for this stream and lane.')
    latest=rows[-1]
    if require_fresh and stream.data_kind=='live':
        minute=int(datetime.now(timezone.utc).timestamp()//60)
        if latest.minute>=minute:raise ValueError('Live data must contain completed past minutes.')
        if minute-latest.minute>2:raise ValueError('Live lane data is stale.')
    model=db.scalar(select(ForecastModel).where(ForecastModel.stream_id==stream_id,
        ForecastModel.lane_id==lane_id,ForecastModel.horizon==horizon).order_by(ForecastModel.created_at.desc()).limit(1))
    if model is None:
        model=db.scalar(select(ForecastModel).join(ForecastStream,ForecastModel.stream_id==ForecastStream.id)
            .where(ForecastStream.source==stream.source,ForecastStream.layout_id==stream.layout_id,
                ForecastStream.data_kind==stream.data_kind,ForecastModel.lane_id==lane_id,ForecastModel.horizon==horizon)
            .order_by(ForecastModel.created_at.desc()).limit(1))
    if model is None:raise ValueError('No trained model for this source/layout, lane and horizon. Submit a training job first.')
    key=hashlib.sha256(f'{stream_id}:{lane_id}:{horizon}:{latest.minute}:{model.id}'.encode()).hexdigest()
    cached=db.scalar(select(ForecastResult).where(ForecastResult.cache_key==key))
    if cached:return dict(json.loads(cached.payload_json),cache_hit=True)
    payload=dict(stream_id=stream_id,lane_id=lane_id,model_id=model.id,horizon_minutes=horizon,
        data_kind=stream.data_kind,data_through_minute=latest.minute,
        target_minute=latest.minute+horizon,time_basis='UTC epoch minute' if stream.data_kind=='live' else 'source-relative minute',
        generated_at=now().isoformat(),predictions=infer(json.loads(model.artifact_json),rows),
        limitations=['Visible vehicle count is not arrival volume.','Vehicle speeds inherit calibration error.',
          'Demonstration/synthetic results do not establish real-world accuracy.','No calibrated confidence interval.'])
    db.add(ForecastResult(cache_key=key,stream_id=stream_id,lane_id=lane_id,model_id=model.id,
                          payload_json=json.dumps(payload,allow_nan=False)))
    try:db.commit()
    except IntegrityError:
        db.rollback()
        cached=db.scalar(select(ForecastResult).where(ForecastResult.cache_key==key))
        if cached:return dict(json.loads(cached.payload_json),cache_hit=True)
        raise
    return dict(payload,cache_hit=False)
