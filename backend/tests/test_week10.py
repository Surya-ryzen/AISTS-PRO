"""Isolated API tests: no live camera, existing database or production model required."""
import io
import os
from types import SimpleNamespace
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

for k, v in dict(APP_NAME='test', APP_ENV='test', DEBUG='false', SECRET_KEY='test-only-not-for-deployment',
    API_HOST='127.0.0.1', API_PORT='8001', DATABASE_URL='sqlite://', LOG_LEVEL='INFO', MODEL_PATH='unused',
    ALLOWED_ORIGINS='http://localhost', PROJECT_NAME='test', VERSION='test').items():
    os.environ.setdefault(k, v)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.database.base import Base
from backend.app.api import week10
from backend.app.dependencies.auth import get_current_user, get_db
from backend.app.services.anpr.recognition import valid_plate, extract_candidates


@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = FastAPI()
    app.include_router(week10.router)
    def db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username='reviewer', role='ADMIN')
    with TestClient(app) as client:
        yield client
    engine.dispose()


@pytest.mark.parametrize('value', ['AP09AB1234','TS08Z9999','DL1CA1234','22BH1234AA','ap 09 ab 1234'])
def test_plate_formats(value):
    assert valid_plate(value)


@pytest.mark.parametrize('value', ['SALE1234','123456','APO9AB1234','AP09AB123','', 'AMBULANCE'])
def test_not_a_plate(value):
    assert not valid_plate(value)


def test_candidate_extraction_preserves_evidence():
    box = [[0,0],[100,0],[100,30],[0,30]]
    plates, events = extract_candidates([(box,'AP 09 AB 1234',.9),(box,'AP09AB1234',.8),
                                         (box,'AMBULANCE',.98),(box,'FIRE SALE',.99),
                                         (box,'TS08AB9876',.4)])
    assert len(plates) == 1 and plates[0]['confidence'] == .9
    assert len(events) == 1 and events[0]['vehicle_type'] == 'ambulance'


def test_no_login_rejected(client):
    client.app.dependency_overrides.pop(get_current_user)
    assert client.get('/week10/plates').status_code == 401
    assert client.get('/week10/emergencies').status_code == 401


def test_reader_cannot_mutate(client):
    client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username='reader', role='USER')
    assert client.get('/week10/plates').status_code == 200
    assert client.post('/week10/emergencies', json={'source':'test','vehicle_type':'ambulance','evidence':'visible markings'}).status_code == 403


def test_workflow_audit_and_stale_version(client):
    r = client.post('/week10/emergencies', json={'source':'test','vehicle_type':'ambulance','evidence':'visible markings'})
    assert r.status_code == 201
    event = r.json()
    path = '/week10/emergencies/' + str(event['id'])
    assert client.patch(path, json={'status':'resolved','note':'not allowed','version':1}).status_code == 409
    r = client.patch(path,json={'status':'acknowledged','note':'visually checked','version':1})
    assert r.status_code == 200 and r.json()['version'] == 2
    assert client.patch(path,json={'status':'rejected','note':'stale edit','version':1}).status_code == 409
    assert client.patch(path,json={'status':'priority_requested','note':'request','version':2}).status_code == 422
    r = client.patch(path,json={'status':'priority_requested','note':'confirmed lane','lane_id':2,'version':2})
    assert r.status_code == 200 and r.json()['lane_id'] == 2
    assert client.patch(path,json={'status':'resolved','note':'vehicle passed','version':3}).status_code == 200
    assert client.patch(path,json={'status':'acknowledged','note':'reopen','version':4}).status_code == 409
    audit = client.get(path+'/audit').json()
    assert [r['to_status'] for r in audit] == ['pending','acknowledged','priority_requested','resolved']
    assert all(r['actor'] == 'reviewer' for r in audit)


def test_analyze_search_review_and_retry(client, monkeypatch):
    output = ([dict(plate='AP09AB1234',raw_text='AP 09 AB 1234',confidence=.9,bbox=[])],
              [dict(vehicle_type='ambulance',confidence=.91,evidence='Visible AMBULANCE')])
    monkeypatch.setattr(week10.recognizer, 'recognize', lambda _: output)
    b = io.BytesIO(); Image.new('RGB',(100,100)).save(b,format='PNG')
    for _ in range(2):
        r = client.post('/week10/analyze',files={'file':('image.png',b.getvalue(),'image/png')},data={'source':'cam1'})
        assert r.status_code == 200
    records = client.get('/week10/plates?q=ap%2009').json()
    assert len(records) == 1 and records[0]['status'] == 'unverified'
    assert len(client.get('/week10/emergencies').json()) == 1
    assert client.get('/week10/plates?source=other').json() == []
    path = '/week10/plates/'+str(records[0]['id'])
    assert client.patch(path,json={'status':'verified','plate':'AP09AB1235'}).status_code == 200
    assert client.get('/week10/plates?q=1235').json()[0]['reviewed_by'] == 'reviewer'
    client.post('/week10/analyze',files={'file':('image.png',b.getvalue(),'image/png')},data={'source':'cam1'})
    assert len(client.get('/week10/plates').json()) == 1
    assert client.patch(path,json={'status':'verified','plate':'invalid'}).status_code == 422


def test_invalid_upload_and_limits(client):
    assert client.post('/week10/analyze',files={'file':('bad.jpg',b'bad','image/jpeg')}).status_code == 400
    assert client.post('/week10/analyze',files={'file':('big.jpg',b'x'*(8*1024*1024+1),'image/jpeg')}).status_code == 413
    assert client.get('/week10/plates?limit=500').status_code == 422
    assert client.get('/week10/plates?start=2026-10-01&end=2026-01-01').status_code == 422


def test_missing_record(client):
    assert client.get('/week10/emergencies/999/audit').status_code == 404
    assert client.patch('/week10/plates/999',json={'status':'rejected'}).status_code == 404


def test_video_sampling(client, monkeypatch, tmp_path):
    import cv2
    import numpy as np
    path = str(tmp_path/'test.mp4')
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), 2, (160,100))
    assert writer.isOpened()
    for _ in range(4):
        writer.write(np.zeros((100,160,3),dtype=np.uint8))
    writer.release()
    monkeypatch.setattr(week10.recognizer,'recognize',lambda _: ([],[]))
    with open(path,'rb') as f:
        result = client.post('/week10/analyze-video',files={'file':('test.mp4',f,'video/mp4')},data={'samples':2})
    assert result.status_code == 200
    assert result.json()['sampled_frames'] == 2 and result.json()['total_frames'] == 4


def test_custom_detector_requires_correct_weights(monkeypatch):
    from backend.app.services.anpr.emergency import EmergencyDetector
    monkeypatch.delenv('WEEK10_EMERGENCY_MODEL', raising=False)
    detector = EmergencyDetector()
    assert detector.detect(None) == []
    monkeypatch.setenv('WEEK10_EMERGENCY_MODEL','missing-model.pt')
    with pytest.raises(RuntimeError, match='local weight file'):
        detector.detect(None)


def test_migration_adds_tables(tmp_path):
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect
    path = Path(__file__).parents[1]/'migrations/versions/c10e20260919_week10_observations.py'
    spec = importlib.util.spec_from_file_location('week10_migration', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    engine = create_engine('sqlite:///'+str(tmp_path/'migration.db'))
    with engine.begin() as connection:
        module.op = Operations(MigrationContext.configure(connection))
        module.upgrade()
        assert set(inspect(connection).get_table_names()) == {'plate_observations','emergency_events','emergency_audit'}
        module.downgrade()
        assert inspect(connection).get_table_names() == []
    engine.dispose()
