"""Consume reviewed requests at the simulated controller's phase boundary."""
from datetime import datetime,timezone
from sqlalchemy import select
from backend.app.database.tables.week10 import EmergencyPriority,EmergencyEvent,EmergencyAudit,EmergencySighting,now
from backend.app.services.decision_engine.models import Decision


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def choose_priority(db,source,run_id,lane_count):
    requests=list(db.scalars(select(EmergencyPriority).where(EmergencyPriority.status=='queued')
        .order_by(EmergencyPriority.created_at,EmergencyPriority.id).with_for_update()))
    for request in requests:
        event=db.scalar(select(EmergencyEvent).where(EmergencyEvent.id==request.event_id).with_for_update())
        sighting=db.scalar(select(EmergencySighting).where(EmergencySighting.event_id==request.event_id)
            .order_by(EmergencySighting.id.desc()).limit(1))
        valid=(event is not None and event.status=='priority_requested' and event.lane_id==request.lane_id
            and request.source==str(source) and request.run_id==run_id and 1<=request.lane_id<=lane_count
            and utc(request.expires_at)>now() and sighting is not None and sighting.run_id==run_id
            and (now()-utc(sighting.observed_at)).total_seconds()<=30)
        if not valid:
            request.status='expired'
            if event:
                if event.status=='priority_requested':event.status='acknowledged';event.version+=1
                db.add(EmergencyAudit(event_id=event.id,actor='signal_scheduler',from_status='priority_requested',
                    to_status=event.status,note='Priority expired or source/lane/sighting no longer matches.'))
            continue
        request.status='applied';request.applied_at=now()
        db.add(EmergencyAudit(event_id=event.id,actor='signal_scheduler',from_status=event.status,to_status=event.status,
            note=f'Simulated green assigned: lane {request.lane_id}, {request.green_seconds} seconds.'))
        return Decision(request.lane_id,request.green_seconds,f'Reviewed emergency {event.id}')
    return None
