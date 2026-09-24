from types import SimpleNamespace
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from backend.tests.test_week10 import client
from backend.app.database.base import Base
from backend.app.database.tables.week10 import EmergencyEvent, EmergencySighting
from backend.app.services.anpr.live import record_sighting, overlap


def test_history_dedup_lane_change_and_run_identity():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    candidate = dict(vehicle_type='ambulance', confidence=.91, evidence='test detector', bbox=[0,0,50,50])
    track = SimpleNamespace(track_id=7)
    with Session(engine) as db:
        first = record_sighting(db, 'camera-1', 'run-1', track, 1, candidate, 1)
        db.commit()
        record_sighting(db, 'camera-1', 'run-1', track, 1, candidate, 1)
        db.commit()
        assert db.scalar(select(func.count()).select_from(EmergencySighting)) == 1
        first.status = 'priority_requested'
        record_sighting(db, 'camera-1', 'run-1', track, 2, candidate, 2)
        db.commit()
        assert first.status == 'acknowledged' and first.lane_id == 2
        record_sighting(db, 'camera-1', 'run-1', track, 3, candidate, None)
        second = record_sighting(db, 'camera-1', 'run-2', track, 1, candidate, 1)
        db.commit()
        assert second.id != first.id
        assert first.lane_id is None
        assert [r.lane_id for r in db.scalars(select(EmergencySighting).where(
            EmergencySighting.event_id == first.id).order_by(EmergencySighting.id))] == [1,2,None]


def test_history_api_missing_and_empty(client):
    assert client.get('/emergencies/999/sightings').status_code == 404
    event = client.post('/emergencies', json=dict(source='camera', vehicle_type='ambulance',
        evidence='Operator observed ambulance', lane_id=1)).json()
    assert client.get(f"/emergencies/{event['id']}/sightings").json() == []


def test_box_matching():
    assert overlap([0,0,10,10], [0,0,10,10]) == 1
    assert overlap([0,0,10,10], [20,20,30,30]) == 0
