import hashlib
import io
import json
from datetime import datetime
from typing import Literal
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.dependencies.auth import get_current_user, require_admin, get_db
from backend.app.database.tables.week10 import PlateObservation, EmergencyEvent, EmergencyAudit, now
from backend.app.services.anpr.recognition import recognizer, normalize_plate, valid_plate

router = APIRouter()


def serialize(row):
    return {col.name: getattr(row, col.name) for col in row.__table__.columns}


@router.get('/week10/status', include_in_schema=False)
@router.get('/ai/status', tags=['AI Processing'], summary='Check recognition capabilities')
def status(user=Depends(get_current_user)):
    import importlib.util
    from backend.app.core.settings import settings
    spec = importlib.util.find_spec('rapidocr_onnxruntime')
    return dict(ocr_installed=bool(spec and spec.origin),
                custom_emergency_model_configured=bool(settings.WEEK10_EMERGENCY_MODEL),
                emergency_method='Visible ambulance/police/fire-rescue text candidates; operator review required',
                limitations=['Emergency candidates require review; experimental weights are not enabled by default',
                             'OCR supports common single-line Indian and BH formats; not all registrations',
                             'Reviewed green-time requests affect the local simulator only; no physical controller integration'],
                live_emergency_history_enabled=True,
                history_identity='Camera-run track ID; cross-camera identity is not established',
                lane_assignment='Saved manual polygons only; otherwise unknown',
                username=user.username, role=user.role)


def persist_scan(db, plates, candidates, source, frame_key, actor):
    # Idempotent retry of the same image/source. Different video frames remain observations.
    previous = db.scalars(select(PlateObservation).where(PlateObservation.frame_key == frame_key,
                                                       PlateObservation.source == source)).all()
    events = db.scalars(select(EmergencyEvent).where(EmergencyEvent.frame_key == frame_key,
                                                    EmergencyEvent.source == source)).all()
    try:
        plate_rows = list(previous)
        seen = {r.raw_text for r in previous}
        for p in plates:
            if p['raw_text'] in seen:
                continue
            row = PlateObservation(source=source, frame_key=frame_key, plate=p['plate'],
                                   raw_text=p['raw_text'], confidence=p['confidence'],
                                   bbox_json=json.dumps(p['bbox']))
            db.add(row)
            plate_rows.append(row)
            seen.add(p['raw_text'])
        kinds = {r.vehicle_type for r in events}
        for candidate in candidates:
            if candidate['vehicle_type'] in kinds:
                continue
            event = EmergencyEvent(source=source, frame_key=frame_key,
                method=candidate.get('method', 'text_candidate'), vehicle_type=candidate['vehicle_type'],
                evidence=candidate['evidence'], confidence=candidate['confidence'])
            db.add(event)
            db.flush()
            db.add(EmergencyAudit(event_id=event.id, actor=actor, from_status='', to_status='pending',
                                  note='Detection candidate; operator verification required'))
            events.append(event)
            kinds.add(candidate['vehicle_type'])
        db.commit()
    except IntegrityError:
        # A concurrent retry stored the same immutable frame evidence.
        db.rollback()
        plate_rows = list(db.scalars(select(PlateObservation).where(
            PlateObservation.source == source, PlateObservation.frame_key == frame_key)))
        events = list(db.scalars(select(EmergencyEvent).where(
            EmergencyEvent.source == source, EmergencyEvent.frame_key == frame_key)))
    return dict(plates=[serialize(r) for r in plate_rows], emergencies=[serialize(r) for r in events])


@router.post('/week10/analyze', include_in_schema=False)
@router.post('/ai/analyze-image', tags=['AI Processing'], summary='Analyze an image')
def analyze(file: UploadFile = File(...), source: str = Form('uploaded-image', max_length=160),
            user=Depends(require_admin), db: Session = Depends(get_db)):
    data = file.file.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, 'Image limit is 8 MB. Use a video frame or crop.')
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.width * im.height > 16_000_000:
                raise HTTPException(413, 'Image limit is 16 megapixels.')
            im.load()
            image = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, 'Upload a valid JPG or PNG image.') from exc
    try:
        plates, emergencies = recognizer.recognize(image)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    result = persist_scan(db, plates, emergencies, source.strip() or 'uploaded-image',
                          hashlib.sha256(data).hexdigest(), user.username)
    result['notice'] = 'Candidates require review. No match does not prove absence. Images are not retained.'
    return result


@router.post('/week10/analyze-video', include_in_schema=False)
@router.post('/ai/analyze-video', tags=['AI Processing'], summary='Analyze sampled video frames')
def analyze_video(file: UploadFile = File(...), source: str = Form('uploaded-video', max_length=160),
                  samples: int = Form(6, ge=1, le=12),
                  user=Depends(require_admin), db: Session = Depends(get_db)):
    """Analyze uniformly sampled frames, not every frame. No video is retained."""
    import os
    import tempfile
    import cv2
    data = file.file.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise HTTPException(413, 'Clip limit is 32 MB. Upload a short clip.')
    digest = hashlib.sha256(data).hexdigest()
    path = None
    capture = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            path = tmp.name
            tmp.write(data)
        capture = cv2.VideoCapture(path)
        count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not capture.isOpened() or count < 1:
            raise HTTPException(400, 'Cannot decode this clip. Try an MP4 with H.264 video.')
        indices = np.linspace(0, count-1, min(samples, count), dtype=int).tolist()
        results = []
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = capture.read()
            if not ok:
                results.append(dict(frame=index, error='Frame could not be decoded'))
                continue
            if frame.shape[0] * frame.shape[1] > 16_000_000:
                raise HTTPException(413, 'Frame limit is 16 megapixels.')
            try:
                plates, events = recognizer.recognize(frame)
            except RuntimeError as exc:
                raise HTTPException(503, str(exc)) from exc
            key = hashlib.sha256((digest+':'+str(index)).encode()).hexdigest()
            results.append(dict(frame=index, **persist_scan(db, plates, events, source, key, user.username)))
        return dict(frames=results, sampled_frames=len(indices), total_frames=count,
                    notice='Only sampled frames analyzed. Records are per-frame candidates, not unique vehicle counts.')
    finally:
        if capture is not None:
            capture.release()
        if path is not None:
            os.unlink(path)


@router.get('/week10/plates', include_in_schema=False)
@router.get('/anpr/plates', tags=['ANPR'], summary='Search plate observations')
def plates(q: str = Query('', max_length=20), source: str | None = Query(None, max_length=160),
           start: datetime | None = None, end: datetime | None = None,
           limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
           user=Depends(get_current_user), db: Session = Depends(get_db)):
    if start and end and start > end:
        raise HTTPException(422, 'Start must precede end.')
    query = select(PlateObservation)
    if q:
        normalized = normalize_plate(q)
        if not normalized:
            raise HTTPException(422, 'Enter letters or digits to search.')
        query = query.where(PlateObservation.plate.contains(normalized, autoescape=True))
    if source:
        query = query.where(PlateObservation.source == source)
    if start:
        query = query.where(PlateObservation.observed_at >= start)
    if end:
        query = query.where(PlateObservation.observed_at <= end)
    return [serialize(r) for r in db.scalars(query.order_by(PlateObservation.id.desc()).limit(limit).offset(offset))]


class PlateReview(BaseModel):
    status: Literal['verified', 'rejected']
    plate: str | None = Field(None, max_length=20)


@router.patch('/week10/plates/{record_id}', include_in_schema=False)
@router.patch('/anpr/plates/{record_id}', tags=['ANPR'], summary='Review a plate observation')
def review_plate(record_id: int, payload: PlateReview, user=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(PlateObservation, record_id)
    if row is None:
        raise HTTPException(404, 'Observation not found.')
    if payload.plate is not None:
        if not valid_plate(payload.plate):
            raise HTTPException(422, 'Use a supported Indian or BH plate format.')
        row.plate = normalize_plate(payload.plate)
    row.status, row.reviewed_by = payload.status, user.username
    db.commit()
    return serialize(row)


class ManualEmergency(BaseModel):
    source: str = Field(min_length=1, max_length=160)
    vehicle_type: Literal['ambulance', 'fire_engine', 'police', 'other']
    evidence: str = Field(min_length=5, max_length=500)
    lane_id: int | None = Field(None, ge=1, le=8)


@router.post('/week10/emergencies', status_code=201, include_in_schema=False)
@router.post('/emergencies', status_code=201, tags=['Emergency Management'], summary='Report an emergency')
def manual_event(payload: ManualEmergency, user=Depends(require_admin), db: Session = Depends(get_db)):
    import uuid
    row = EmergencyEvent(**payload.model_dump(), method='operator_report', frame_key=uuid.uuid4().hex)
    db.add(row)
    db.flush()
    db.add(EmergencyAudit(event_id=row.id, actor=user.username, from_status='', to_status='pending',
                          note='Operator report: ' + payload.evidence[:450]))
    db.commit()
    return serialize(row)


@router.get('/week10/emergencies', include_in_schema=False)
@router.get('/emergencies', tags=['Emergency Management'], summary='List emergency events')
def emergencies(state: Literal['pending','acknowledged','priority_requested','resolved','rejected'] | None = None,
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(EmergencyEvent)
    if state:
        query = query.where(EmergencyEvent.status == state)
    return [serialize(r) for r in db.scalars(query.order_by(EmergencyEvent.id.desc()).limit(limit).offset(offset))]


TRANSITIONS = {'pending': {'acknowledged', 'rejected'},
               'acknowledged': {'priority_requested', 'resolved', 'rejected'},
               'priority_requested': {'resolved', 'rejected'}, 'resolved': set(), 'rejected': set()}


class Transition(BaseModel):
    status: Literal['acknowledged', 'priority_requested', 'resolved', 'rejected']
    note: str = Field(min_length=3, max_length=500)
    version: int = Field(ge=1)
    lane_id: int | None = Field(None, ge=1, le=8)


@router.patch('/week10/emergencies/{event_id}', include_in_schema=False)
@router.patch('/emergencies/{event_id}', tags=['Emergency Management'], summary='Update emergency status')
def transition(event_id: int, payload: Transition, user=Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(EmergencyEvent, event_id)
    if row is None:
        raise HTTPException(404, 'Event not found.')
    if payload.version != row.version or payload.status not in TRANSITIONS[row.status]:
        raise HTTPException(409, 'Event changed or transition not allowed. Refresh first.')
    lane = payload.lane_id or row.lane_id
    if payload.status == 'priority_requested' and lane is None:
        raise HTTPException(422, 'Select a reviewed lane before requesting priority.')
    before = row.status
    changed = db.execute(update(EmergencyEvent).where(EmergencyEvent.id == event_id,
                            EmergencyEvent.version == payload.version).values(status=payload.status,
                            lane_id=lane, version=payload.version + 1, updated_at=now()))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Concurrent update. Refresh first.')
    db.add(EmergencyAudit(event_id=event_id, actor=user.username, from_status=before,
                          to_status=payload.status, note=payload.note))
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get('/week10/emergencies/{event_id}/audit', include_in_schema=False)
@router.get('/emergencies/{event_id}/audit', tags=['Emergency Management'], summary='View emergency audit history')
def audit(event_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if db.get(EmergencyEvent, event_id) is None:
        raise HTTPException(404, 'Event not found.')
    return [serialize(r) for r in db.scalars(select(EmergencyAudit).where(EmergencyAudit.event_id == event_id)
                                           .order_by(EmergencyAudit.id))]


@router.get('/emergencies/{event_id}/sightings', tags=['Emergency Management'],
            summary='Vehicle sightings and lane history within one camera run')
def sightings(event_id: int, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
              user=Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.app.database.tables.week10 import EmergencySighting
    if db.get(EmergencyEvent, event_id) is None:
        raise HTTPException(404, 'Event not found.')
    return [serialize(r) for r in db.scalars(select(EmergencySighting)
        .where(EmergencySighting.event_id == event_id).order_by(EmergencySighting.id)
        .limit(limit).offset(offset))]


class GreenRequest(BaseModel):
    version: int = Field(ge=1)
    green_seconds: int = Field(ge=10,le=60)
    note: str = Field(min_length=3,max_length=400)


@router.post('/emergencies/{event_id}/priority',status_code=201,tags=['Emergency Management'])
def request_green(event_id:int,payload:GreenRequest,user=Depends(require_admin),db:Session=Depends(get_db)):
    from datetime import timedelta
    from backend.app.database.tables.week10 import EmergencyPriority,EmergencySighting
    from backend.app.services.anpr.priority import utc
    event=db.scalar(select(EmergencyEvent).where(EmergencyEvent.id==event_id).with_for_update())
    if event is None:raise HTTPException(404,'Event not found.')
    if event.version!=payload.version or event.status not in ('acknowledged','priority_requested'):
        raise HTTPException(409,'Acknowledge the latest event before requesting green time.')
    if not event.lane_id:raise HTTPException(422,'A reviewed lane is required.')
    sighting=db.scalar(select(EmergencySighting).where(EmergencySighting.event_id==event_id)
        .order_by(EmergencySighting.id.desc()).limit(1))
    if not sighting or (now()-utc(sighting.observed_at)).total_seconds()>30:
        raise HTTPException(422,'A fresh tracked sighting within 30 seconds is required.')
    pending=db.scalar(select(EmergencyPriority).where(EmergencyPriority.event_id==event_id,
        EmergencyPriority.status=='queued'))
    if pending:raise HTTPException(409,'A green-time request is already queued for this event.')
    before=event.status;event.status='priority_requested';event.version+=1;event.updated_at=now()
    row=EmergencyPriority(event_id=event_id,event_version=event.version,source=event.source,
        run_id=sighting.run_id,lane_id=event.lane_id,green_seconds=payload.green_seconds,actor=user.username,
        expires_at=now()+timedelta(seconds=120))
    db.add(row);db.add(EmergencyAudit(event_id=event_id,actor=user.username,from_status=before,
        to_status=event.status,note=f'Requested {payload.green_seconds}s simulated green: {payload.note}'))
    db.commit();return serialize(row)


@router.get('/emergencies/{event_id}/priority',tags=['Emergency Management'])
def priority_history(event_id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    from backend.app.database.tables.week10 import EmergencyPriority
    return [serialize(r) for r in db.scalars(select(EmergencyPriority)
        .where(EmergencyPriority.event_id==event_id).order_by(EmergencyPriority.id.desc()).limit(100))]


@router.get('/anpr/vehicles/{plate}/history',tags=['ANPR'])
def vehicle_history(plate:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    from backend.app.database.tables.week10 import EmergencyPlateLink
    if not valid_plate(plate):raise HTTPException(422,'Unsupported registration format.')
    query=select(EmergencyEvent).join(EmergencyPlateLink,EmergencyPlateLink.event_id==EmergencyEvent.id)
    query=query.join(PlateObservation,PlateObservation.id==EmergencyPlateLink.plate_id).where(
        PlateObservation.plate==normalize_plate(plate),PlateObservation.status=='verified').distinct()
    return dict(plate=normalize_plate(plate),identity_basis='operator-verified plate observations',
        emergencies=[serialize(r) for r in db.scalars(query.order_by(EmergencyEvent.id.desc()).limit(200))])
