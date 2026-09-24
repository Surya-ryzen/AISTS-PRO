from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
import json
import numpy as np
import pytest
from sqlalchemy import create_engine,select,func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.tests.test_week10 import client
from backend.app.database.base import Base
from backend.app.database.tables.forecasting import *
from backend.app.database.tables.week10 import *
from backend.app.services.prediction.model import train,infer
from backend.app.services.prediction.runtime import run_job,forecast_stream
from backend.app.services.anpr.priority import choose_priority
from backend.app.services.anpr.live import record_sighting,save_plate_links
from backend.app.services.anpr.recognition import extract_candidates


def sample_rows(n=180):
    return [SimpleNamespace(minute=i,vehicle_count=20+np.sin(i/10)*5,
        average_speed=30+np.cos(i/13)*3,queue_length=2+np.sin(i/10)) for i in range(n)]


@pytest.fixture
def factory():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine,expire_on_commit=False)
    engine.dispose()


@pytest.mark.parametrize('horizon',[1,5,15])
def test_train_and_explain(horizon):
    data=sample_rows();model=train(data,horizon);result=infer(model,data[-6:])
    assert model['evaluation']['test_samples']>=5
    assert all(m>=144 for m in model['evaluation']['test_target_minutes'])
    for item in result.values():
        e=item['explanation']
        assert abs(item['value']-(e['intercept']+sum(c['value'] for c in e['contributions'])+e['nonnegative_adjustment']))<1e-8
        assert item['value']>=0


def test_gap_small_and_nonfinite_rejected():
    with pytest.raises(ValueError):train(sample_rows(30),1)
    data=sample_rows();data[10].minute+=2
    with pytest.raises(ValueError):train(data,1)
    data=sample_rows();data[10].vehicle_count=float('nan')
    with pytest.raises(ValueError):train(data,1)


def test_training_job_database_cache_and_history(factory):
    with factory() as db:
        db.add(ForecastStream(id='s',source='test',run_id='r',layout_id='l',data_kind='synthetic'))
        for r in sample_rows():db.add(ForecastSample(stream_id='s',lane_id=1,**vars(r)))
        db.add(ForecastJob(id='j',stream_id='s',lane_id=1,horizon=5));db.commit()
    run_job('j',factory)
    with factory() as db:
        job=db.get(ForecastJob,'j');assert job.status=='succeeded' and job.model_id
        first=forecast_stream(db,'s',1,5);second=forecast_stream(db,'s',1,5)
        assert not first['cache_hit'] and second['cache_hit']
        assert first['model_id']==second['model_id']
        assert db.scalar(select(func.count()).select_from(ForecastResult))==1
        db.add(ForecastSample(stream_id='s',lane_id=1,minute=180,vehicle_count=20,average_speed=30,queue_length=2));db.commit()
        assert not forecast_stream(db,'s',1,5)['cache_hit']
        with pytest.raises(ValueError):forecast_stream(db,'s',2,5)
    run_job('j',factory)  # Completed jobs are not repeated.
    with factory() as db:assert db.scalar(select(func.count()).select_from(ForecastModel))==1


def test_failed_job_reports_insufficient_data(factory):
    with factory() as db:
        db.add(ForecastJob(id='j',stream_id='empty',lane_id=1,horizon=1));db.commit()
    run_job('j',factory)
    with factory() as db:
        job=db.get(ForecastJob,'j');assert job.status=='failed' and 'consecutive' in job.error


def test_priority_freshness_lane_and_audit(factory):
    with factory() as db:
        candidate=dict(vehicle_type='ambulance',confidence=.9,evidence='test',bbox=[0,0,100,100])
        event=record_sighting(db,'camera','run',SimpleNamespace(track_id=1),1,candidate,1)
        event.status='priority_requested'
        db.add(EmergencyPriority(event_id=event.id,event_version=event.version,source='camera',run_id='run',
            lane_id=1,green_seconds=25,actor='test',expires_at=now()+timedelta(seconds=120)))
        db.commit()
        decision=choose_priority(db,'camera','run',2);db.commit()
        assert decision.green_time==25 and decision.selected_lane==1
        assert choose_priority(db,'camera','run',2) is None
        event.status='priority_requested'
        db.add(EmergencyPriority(event_id=event.id,event_version=event.version,source='camera',run_id='old-run',
            lane_id=1,green_seconds=25,actor='test',expires_at=now()+timedelta(seconds=120)));db.commit()
        assert choose_priority(db,'camera','run',2) is None
        db.commit();assert event.status=='acknowledged'


def test_police_and_fire_text_candidates():
    box=[[0,0],[100,0],[100,20],[0,20]]
    _,events=extract_candidates([(box,'POLICE',.9),(box,'FIRE SERVICE',.95),(box,'FIRE SALE',.99)])
    assert [e['vehicle_type'] for e in events]==['police','fire_engine']


def test_signal_has_yellow_and_all_red(monkeypatch):
    import backend.app.services.traffic_signal.service as module
    from backend.app.services.traffic_signal.models import SignalState
    clock=[0.];monkeypatch.setattr(module.time,'monotonic',lambda:clock[0])
    signal=module.TrafficSignalService();clock[0]=30
    assert not signal.update() and signal.signal.state==SignalState.YELLOW
    clock[0]+=5;assert not signal.update() and signal.signal.state==SignalState.RED
    clock[0]+=2;assert signal.update()


def test_forecast_api_import_idempotence_and_auth(client):
    from backend.app.api.forecasting import router
    client.app.include_router(router)
    body=dict(source='fixture',run_id='one',layout_id='layout',data_kind='synthetic')
    response=client.post('/forecasting/streams',json=body);assert response.status_code==201
    sid=response.json()['id'];assert client.post('/forecasting/streams',json=body).json()['id']==sid
    point=dict(lane_id=1,minute=0,vehicle_count=10,average_speed=20,queue_length=2)
    path=f'/forecasting/streams/{sid}/samples'
    assert client.post(path,json={'samples':[point]}).json()['inserted']==1
    assert client.post(path,json={'samples':[point]}).json()['inserted']==0
    assert client.post(path,json={'samples':[dict(point,vehicle_count=11)]}).status_code==409
    assert client.get(f'/forecasting/streams/{sid}/lanes/1').status_code==503
    assert client.get(f'/forecasting/streams/{sid}/lanes/1?horizon=2').status_code==422
    for h in (1,5,15):assert client.get(f'/forecasting/streams/{sid}/lanes/1?horizon={h}').status_code==503
    client.app.dependency_overrides.clear()
    assert client.get('/forecasting/streams').status_code==401


def test_collector_source_time_and_loop_isolation(monkeypatch):
    from backend.app.services.prediction.collection import ForecastCollector
    collector=ForecastCollector();saved=[]
    monkeypatch.setattr(collector,'flush',lambda:saved.append((collector.stream_id,collector.bucket)))
    lane=SimpleNamespace(lane_id=1,vehicle_count=4,average_speed=20,queue_length=1)
    profile={'lanes':[[[0,0],[1,0],[1,1]]]}
    def frame(second,loop=0):return SimpleNamespace(source_seconds=second,timestamp=100000+second,loop_index=loop)
    for loop in range(3):
        for sec in (0,10,20,28):collector.process(frame(sec,loop),[lane],'clip',profile)
    assert saved==[]
    for sec in (0,10,20,30,40,50,59,60):collector.process(frame(sec,3),[lane],'clip',profile)
    assert len(saved)==1 and saved[0][1]==0
    old=collector.stream_id
    collector.process(frame(61,3),[lane],'clip',dict(profile,revision=2))
    assert collector.stream_id!=old


def test_live_future_import_rejected(client):
    import time
    from backend.app.api.forecasting import router
    client.app.include_router(router)
    sid=client.post('/forecasting/streams',json=dict(source='camera',run_id='r',layout_id='l',data_kind='live')).json()['id']
    response=client.post(f'/forecasting/streams/{sid}/samples',json={'samples':[dict(lane_id=1,minute=int(time.time()//60)+1,vehicle_count=1,average_speed=2,queue_length=0)]})
    assert response.status_code==422
    assert client.get('/forecasting/streams/missing/history').status_code==404


def test_forecast_model_reuse_isolates_data_kind_and_layout(factory):
    with factory() as db:
        db.add(ForecastStream(id='train',source='camera',run_id='r',layout_id='l',data_kind='synthetic'))
        db.add(ForecastModel(id='m',stream_id='train',lane_id=1,horizon=1,trained_through=179,artifact_json=json.dumps(train(sample_rows(),1))))
        for sid,kind,layout in [('same','synthetic','l'),('changed','synthetic','other'),('real','live','l')]:
            db.add(ForecastStream(id=sid,source='camera',run_id=sid,layout_id=layout,data_kind=kind))
            for r in sample_rows()[-6:]:db.add(ForecastSample(stream_id=sid,lane_id=1,**vars(r)))
        db.commit()
        assert forecast_stream(db,'same',1,1)['model_id']=='m'
        for sid in ('changed','real'):
            with pytest.raises(ValueError,match='No trained model'):forecast_stream(db,sid,1,1,require_fresh=False)


def test_week11_migration_round_trip():
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect
    path=Path(__file__).parents[1]/'migrations/versions/w11_20260924_forecasting.py'
    spec=importlib.util.spec_from_file_location('migration',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=create_engine('sqlite://')
    with engine.begin() as connection:
        module.op=Operations(MigrationContext.configure(connection));module.upgrade()
        assert len(inspect(connection).get_table_names())==7
        module.downgrade();assert inspect(connection).get_table_names()==[]
    engine.dispose()
