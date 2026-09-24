"""Store tracked emergency candidates without changing signal phases."""
import hashlib
import json
import logging
import os
import time
import uuid
from sqlalchemy import select
from backend.app.database.tables.week10 import EmergencyEvent, EmergencyAudit, EmergencySighting, now
from backend.app.database.session_manager import get_db_session
from backend.app.services.anpr.emergency import detector


def overlap(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0


def record_sighting(db, source, run_id, track, frame_id, candidate, lane_id):
    key = hashlib.sha256(f'{run_id}:{track.track_id}'.encode()).hexdigest()
    event = db.scalar(select(EmergencyEvent).where(EmergencyEvent.source == source,
                                                 EmergencyEvent.frame_key == key).with_for_update())
    if event is None:
        event = EmergencyEvent(source=source, frame_key=key, vehicle_type=candidate['vehicle_type'],
            confidence=candidate['confidence'], evidence=candidate['evidence'][:500],
            method=candidate.get('method','tracked_custom_detector'), lane_id=lane_id)
        db.add(event)
        db.flush()
        db.add(EmergencyAudit(event_id=event.id, actor='live_detector', from_status='', to_status='pending',
                             note='Tracked vehicle candidate; review before priority.'))
    existing = db.scalar(select(EmergencySighting.id).where(EmergencySighting.event_id == event.id,
                                                           EmergencySighting.frame_id == frame_id))
    if existing is not None:
        return event
    if event.lane_id != lane_id:
        before = event.status
        # A prior priority request is tied to its reviewed lane. Require review again after movement.
        if event.status == 'priority_requested':
            event.status = 'acknowledged'
        db.add(EmergencyAudit(event_id=event.id, actor='live_detector', from_status=before,
            to_status=event.status, note=f'Lane changed from {event.lane_id} to {lane_id}; recheck priority.'))
    event.lane_id = lane_id
    event.updated_at = now()
    event.version += 1
    db.add(EmergencySighting(event_id=event.id, run_id=run_id, track_id=track.track_id,
        frame_id=frame_id, lane_id=lane_id, confidence=candidate['confidence'],
        bbox_json=json.dumps(candidate['bbox'])))
    return event


from concurrent.futures import ThreadPoolExecutor
from copy import copy
from backend.app.database.tables.week10 import PlateObservation, EmergencyPlateLink
from backend.app.services.anpr.recognition import recognizer
_executor = ThreadPoolExecutor(max_workers=1,thread_name_prefix='emergency-recognition')


def save_plate_links(db,event,plates,source,run_id,track_id,frame_id):
    for p in plates:
        key=hashlib.sha256(f'{run_id}:{track_id}:{frame_id}'.encode()).hexdigest()
        row=db.scalar(select(PlateObservation).where(PlateObservation.source==source,
            PlateObservation.frame_key==key,PlateObservation.raw_text==p['raw_text']))
        if row is None:
            row=PlateObservation(source=source,frame_key=key,plate=p['plate'],raw_text=p['raw_text'],
                confidence=p['confidence'],bbox_json=json.dumps(p['bbox']))
            db.add(row);db.flush()
        if event is not None and not db.scalar(select(EmergencyPlateLink.id).where(
                EmergencyPlateLink.event_id==event.id,EmergencyPlateLink.plate_id==row.id)):
            db.add(EmergencyPlateLink(event_id=event.id,plate_id=row.id))


class LiveEmergencyRecorder:
    def __init__(self):
        self.run_id=uuid.uuid4().hex;self.last_scan=0.;self.future=None;self.cursor=0
        self.error=None;self.completed_scans=0

    def process(self,image,tracks,frame_id,source,manual_lanes):
        if self.future is not None and not self.future.done():return
        if not tracks or time.monotonic()-self.last_scan<2:return
        self.last_scan=time.monotonic()
        self.future=_executor.submit(self.scan,image.copy(),[copy(t) for t in tracks],frame_id,str(source),manual_lanes)

    def scan(self,image,tracks,frame_id,source,manual_lanes):
        try:
            from backend.app.core.settings import settings
            if os.getenv('WEEK10_EMERGENCY_MODEL',settings.WEEK10_EMERGENCY_MODEL):
                candidates=detector.detect(image);used=set()
                for candidate in sorted(candidates,key=lambda c:c['confidence'],reverse=True):
                    matches=sorted([(overlap(candidate['bbox'],[t.x1,t.y1,t.x2,t.y2]),t) for t in tracks],
                        key=lambda p:p[0],reverse=True)
                    if not matches or matches[0][0]<.3:continue
                    score,track=matches[0]
                    if track.track_id in used or (len(matches)>1 and score-matches[1][0]<.1):continue
                    used.add(track.track_id)
                    with get_db_session() as db:
                        record_sighting(db,source,self.run_id,track,frame_id,candidate,track.lane_id if manual_lanes else None)
            # Rotate over a bounded set of tracked crops; OCR cannot establish active siren use.
            selected=[tracks[(self.cursor+i)%len(tracks)] for i in range(min(4,len(tracks)))]
            self.cursor=(self.cursor+len(selected))%len(tracks)
            h,w=image.shape[:2]
            for track in selected:
                x1,y1,x2,y2=max(0,int(track.x1)),max(0,int(track.y1)),min(w,int(track.x2)),min(h,int(track.y2))
                if x2-x1<40 or y2-y1<30:continue
                plates,candidates=recognizer.recognize(image[y1:y2,x1:x2],include_detector=False)
                for p in plates:
                    p['bbox']=[[x+x1,y+y1] for x,y in p['bbox']]
                with get_db_session() as db:
                    event=None
                    if candidates:
                        candidate=max(candidates,key=lambda c:c['confidence'])
                        candidate=dict(candidate,bbox=[x1,y1,x2,y2],method='tracked_text_candidate')
                        event=record_sighting(db,source,self.run_id,track,frame_id,candidate,
                                               track.lane_id if manual_lanes else None)
                    else:
                        key=hashlib.sha256(f'{self.run_id}:{track.track_id}'.encode()).hexdigest()
                        event=db.scalar(select(EmergencyEvent).where(EmergencyEvent.source==source,
                                                                      EmergencyEvent.frame_key==key))
                        if event:
                            candidate=dict(vehicle_type=event.vehicle_type,confidence=event.confidence or 0,
                                evidence='Previously recognized track',bbox=[x1,y1,x2,y2])
                            record_sighting(db,source,self.run_id,track,frame_id,candidate,
                                             track.lane_id if manual_lanes else None)
                    save_plate_links(db,event,plates,source,self.run_id,track.track_id,frame_id)
            self.completed_scans+=1;self.error=None
        except Exception:
            self.error='Recognition failed; check backend logs.'
            logging.getLogger(__name__).exception('Emergency recognition failed; preview continues')
