"""Aggregate complete minutes, never treating looped clips as fresh hours of training data."""
import hashlib,json,uuid,logging
from sqlalchemy import select
from backend.app.database.session_manager import get_db_session
from backend.app.database.tables.forecasting import ForecastStream,ForecastSample
from .runtime import forecast_stream


class ForecastCollector:
    def __init__(self):
        self.run=uuid.uuid4().hex;self.context=None;self.bucket=None;self.values={};self.first=None;self.last=None

    def process(self,frame,lanes,source,profile):
        if not profile or not profile.get('lanes') or profile.get('disabled'):return
        layout=hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()
        kind='recorded' if frame.source_seconds is not None else 'live'
        context=(str(source),layout,frame.loop_index,kind)
        stamp=frame.source_seconds if kind=='recorded' else frame.timestamp
        minute=int(stamp//60)
        if context!=self.context:
            self.context=context;self.stream_id=uuid.uuid4().hex;self.bucket=None;self.values={}
            self.first=None;self.last=None;self.registered=False
        if self.bucket is not None and minute!=self.bucket:
            if self.first-self.bucket*60<=5 and self.last-self.first>=50:
                self.flush()
            self.values={};self.first=None;self.last=None
        self.bucket=minute
        # Limit observations to one per source second to avoid over-weighting slow processing.
        if self.last is not None and int(stamp)==int(self.last):return
        if self.first is None:self.first=stamp
        self.last=stamp
        for lane in lanes:
            self.values.setdefault(lane.lane_id,[]).append([lane.vehicle_count,lane.average_speed,lane.queue_length])

    def flush(self):
        try:
            with get_db_session() as db:
                if not self.registered:
                    source,layout,loop,kind=self.context
                    db.add(ForecastStream(id=self.stream_id,source=source,layout_id=layout,
                        run_id=f'{self.run}:{loop}',data_kind=kind));db.flush()
                for lane,values in self.values.items():
                    mean=[sum(v[i] for v in values)/len(values) for i in range(3)]
                    db.add(ForecastSample(stream_id=self.stream_id,lane_id=lane,minute=self.bucket,
                        vehicle_count=mean[0],average_speed=mean[1],queue_length=mean[2]))
            self.registered=True
            # Completed input minutes trigger forecast generation when a model is available.
            for lane in self.values:
                with get_db_session() as db:
                    for horizon in (1,5,15):
                        try:forecast_stream(db,self.stream_id,lane,horizon)
                        except (ValueError,LookupError):pass
        except Exception:
            logging.getLogger(__name__).exception('Forecast collection failed')
