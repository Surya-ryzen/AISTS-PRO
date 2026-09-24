"""Explainable short-horizon baseline; demo data is not deployment validation."""
from datetime import datetime, timedelta, timezone
from threading import Lock
import time
from sqlalchemy import select
from backend.app.database.tables.lane_analytics import LaneAnalytics

METRICS = ('vehicle_count', 'average_speed', 'queue_length')
ALPHA = 0.4
CACHE_SECONDS = 30
_cache = {}
_lock = Lock()


def smooth(values):
    estimate = float(values[0])
    for value in values[1:]:
        estimate = ALPHA * value + (1-ALPHA) * estimate
    return estimate


def build_forecast(rows, lane_id, current_time):
    if current_time.tzinfo:
        current_time = current_time.astimezone(timezone.utc).replace(tzinfo=None)
    # Use only completed UTC minute buckets; never invent missing measurements.
    cutoff = current_time.replace(second=0, microsecond=0)
    buckets = {}
    for row in rows:
        stamp = row.timestamp
        if stamp.tzinfo:
            stamp = stamp.astimezone(timezone.utc).replace(tzinfo=None)
        minute = stamp.replace(second=0, microsecond=0)
        if minute < cutoff:
            buckets.setdefault(minute, []).append(row)
    if not buckets:
        raise ValueError('No completed minute of lane measurements is available.')
    latest = max(buckets)
    if (cutoff-latest).total_seconds() > 60:
        raise ValueError('Lane measurements are stale; start the camera and check lane setup.')
    minutes = []
    cursor = latest
    while cursor in buckets and len(minutes) < 30:
        minutes.append(cursor)
        cursor -= timedelta(minutes=1)
    minutes.reverse()
    if len(minutes) < 6:
        raise ValueError('Need at least six consecutive completed minutes of lane measurements.')
    series = {metric: [sum(float(getattr(r, metric)) for r in buckets[m])/len(buckets[m])
                       for m in minutes] for metric in METRICS}
    weights = [(1-ALPHA)**(len(minutes)-1)] + [ALPHA*(1-ALPHA)**i for i in range(len(minutes)-2,-1,-1)]
    predictions = {}
    for metric, values in series.items():
        errors = [abs(smooth(values[:i])-values[i]) for i in range(6,len(values))]
        naive_errors = [abs(values[i-1]-values[i]) for i in range(6,len(values))]
        predictions[metric] = dict(value=round(smooth(values),3),
            unit='km/h' if metric == 'average_speed' else 'vehicles',
            target='mean observed value over the next minute',
            explanation=[dict(minute=m.isoformat()+'Z',observed_mean=round(v,3),
                              weight=round(w,6),contribution=round(v*w,6))
                         for m,v,w in zip(minutes,values,weights)],
            backtest=dict(samples=len(errors),
                mae=round(sum(errors)/len(errors),3) if errors else None,
                last_value_baseline_mae=round(sum(naive_errors)/len(naive_errors),3) if errors else None,
                method='Expanding-window one-minute-ahead evaluation; no future observations used'))
    target_start = latest+timedelta(minutes=1)
    return dict(lane_id=lane_id,model='exponentially_weighted_mean_v1',alpha=ALPHA,
        status='experimental_baseline',generated_at=current_time.isoformat()+'Z',
        data_through=(latest+timedelta(minutes=1)).isoformat()+'Z',
        forecast_start=target_start.isoformat()+'Z',
        forecast_end=(target_start+timedelta(minutes=1)).isoformat()+'Z',
        horizon_seconds=60,minutes_used=len(minutes),predictions=predictions,
        limitations=['Demo-video measurements; not validated for real-world forecasting.',
            'Legacy history lacks camera/run/layout identity; do not compare lanes across configurations.',
            'Vehicle count is visible occupancy count, not arriving traffic volume.',
            'No calibrated confidence interval; speed inherits camera-calibration limitations.'])


def forecast(db, lane_id):
    current = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = list(db.scalars(select(LaneAnalytics).where(LaneAnalytics.lane_id == lane_id,
        LaneAnalytics.timestamp >= current-timedelta(minutes=32),
        LaneAnalytics.timestamp <= current).order_by(LaneAnalytics.timestamp, LaneAnalytics.id)))
    key = (lane_id, rows[-1].id if rows else None, current.replace(second=0,microsecond=0))
    with _lock:
        entry = _cache.get(lane_id)
        if entry and entry[0] == key and time.monotonic()-entry[1] < CACHE_SECONDS:
            return dict(entry[2],cache_hit=True)
    result = build_forecast(rows,lane_id,current)
    with _lock:
        _cache[lane_id] = (key,time.monotonic(),result)
    return dict(result,cache_hit=False)
