import hashlib
import json
import uuid
import time
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks,Query,Path
from pydantic import BaseModel,Field,ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.dependencies.auth import get_db,get_current_user,require_admin
from backend.app.database.tables.forecasting import ForecastStream,ForecastSample,ForecastJob,ForecastModel,ForecastResult
from backend.app.services.prediction.runtime import run_job,forecast_stream

router=APIRouter(prefix='/forecasting',tags=['Forecasting'])


class StreamInput(BaseModel):
    source: str=Field(min_length=1,max_length=500)
    run_id: str=Field(min_length=1,max_length=64)
    layout_id: str=Field(min_length=1,max_length=64)
    data_kind: Literal['live','recorded','synthetic']


class SampleInput(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    lane_id: int=Field(ge=1,le=8)
    minute: int=Field(ge=0)
    vehicle_count: float=Field(ge=0,le=10000)
    average_speed: float=Field(ge=0,le=300)
    queue_length: float=Field(ge=0,le=10000)


class SamplesInput(BaseModel):
    samples: list[SampleInput]=Field(min_length=1,max_length=5000)


class TrainInput(BaseModel):
    lane_id: int=Field(ge=1,le=8)
    horizon: Literal[1,5,15]=1


@router.post('/streams',status_code=201)
def create_stream(payload:StreamInput,user=Depends(require_admin),db:Session=Depends(get_db)):
    identity=hashlib.sha256(json.dumps(payload.model_dump(),sort_keys=True).encode()).hexdigest()[:32]
    row=db.get(ForecastStream,identity)
    if row is None:
        row=ForecastStream(id=identity,**payload.model_dump());db.add(row)
        try:db.commit()
        except IntegrityError:
            db.rollback();row=db.get(ForecastStream,identity)
            if row is None:raise
    return dict(id=row.id,**payload.model_dump())


@router.get('/streams')
def streams(user=Depends(get_current_user),db:Session=Depends(get_db),limit:int=Query(50,ge=1,le=200)):
    return [dict(id=r.id,source=r.source,run_id=r.run_id,layout_id=r.layout_id,data_kind=r.data_kind)
        for r in db.scalars(select(ForecastStream).order_by(ForecastStream.created_at.desc()).limit(limit))]


@router.post('/streams/{stream_id}/samples')
def samples(stream_id:str,payload:SamplesInput,user=Depends(require_admin),db:Session=Depends(get_db)):
    stream=db.scalar(select(ForecastStream).where(ForecastStream.id==stream_id).with_for_update())
    if stream is None:raise HTTPException(404,'Stream not found.')
    if stream.data_kind=='live' and any(p.minute>=int(time.time()//60) for p in payload.samples):
        raise HTTPException(422,'Live samples must represent completed past UTC minutes.')
    added=0
    # Rows are immutable so cached forecasts cannot silently outlive corrected inputs.
    for item in payload.samples:
        row=db.scalar(select(ForecastSample).where(ForecastSample.stream_id==stream_id,
            ForecastSample.lane_id==item.lane_id,ForecastSample.minute==item.minute))
        if row:
            if any(getattr(row,k)!=v for k,v in item.model_dump().items()):
                raise HTTPException(409,'Conflicting sample. Import corrected data as a new stream version.')
        else:
            db.add(ForecastSample(stream_id=stream_id,**item.model_dump()));db.flush();added+=1
    db.commit();return dict(inserted=added)


@router.post('/streams/{stream_id}/train',status_code=202)
def submit(stream_id:str,payload:TrainInput,tasks:BackgroundTasks,user=Depends(require_admin),db:Session=Depends(get_db)):
    stream=db.scalar(select(ForecastStream).where(ForecastStream.id==stream_id).with_for_update())
    if stream is None:raise HTTPException(404,'Stream not found.')
    pending=db.scalar(select(ForecastJob).where(ForecastJob.stream_id==stream_id,
        ForecastJob.lane_id==payload.lane_id,ForecastJob.horizon==payload.horizon,
        ForecastJob.status.in_(['queued','running'])))
    if pending:return dict(job_id=pending.id,status=pending.status)
    job=ForecastJob(id=uuid.uuid4().hex,stream_id=stream_id,**payload.model_dump())
    db.add(job);db.commit();tasks.add_task(run_job,job.id)
    return dict(job_id=job.id,status='queued')


@router.get('/jobs/{job_id}')
def job_status(job_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(ForecastJob,job_id)
    if r is None:raise HTTPException(404,'Job not found.')
    return dict(id=r.id,status=r.status,model_id=r.model_id,error=r.error)


@router.get('/models/{model_id}')
def model_status(model_id:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    r=db.get(ForecastModel,model_id)
    if r is None:raise HTTPException(404,'Model not found.')
    return dict(id=r.id,stream_id=r.stream_id,lane_id=r.lane_id,trained_through=r.trained_through,
                artifact=json.loads(r.artifact_json))


@router.get('/streams/{stream_id}/lanes/{lane_id}')
def prediction(stream_id:str,lane_id:int=Path(ge=1,le=8),horizon:int=Query(1,ge=1,le=15),
               user=Depends(get_current_user),db:Session=Depends(get_db)):
    if horizon not in (1,5,15):raise HTTPException(422,'Supported horizons are 1, 5 and 15 minutes.')
    try:return forecast_stream(db,stream_id,lane_id,horizon)
    except LookupError as exc:raise HTTPException(404,str(exc)) from exc
    except ValueError as exc:raise HTTPException(503,str(exc)) from exc


@router.get('/streams/{stream_id}/history')
def history(stream_id:str,limit:int=Query(50,ge=1,le=200),user=Depends(get_current_user),db:Session=Depends(get_db)):
    if db.get(ForecastStream,stream_id) is None:raise HTTPException(404,'Stream not found.')
    return [dict(id=r.id,**json.loads(r.payload_json)) for r in db.scalars(select(ForecastResult)
        .where(ForecastResult.stream_id==stream_id).order_by(ForecastResult.id.desc()).limit(limit))]
