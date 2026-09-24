from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from backend.tests.test_week10 import client
from backend.app.services.prediction.service import build_forecast, smooth
from backend.app.api.predictions import router

NOW = datetime(2026,9,23,12,30,15)


def rows(n=12):
    return [SimpleNamespace(timestamp=NOW.replace(second=0)-timedelta(minutes=n-i),
        vehicle_count=10,average_speed=20,queue_length=2) for i in range(n)]


def test_constant_forecast_and_explanation():
    result=build_forecast(rows(),1,NOW)
    item=result['predictions']['vehicle_count']
    assert item['value']==10
    assert abs(sum(x['weight'] for x in item['explanation'])-1)<.00001
    assert abs(sum(x['contribution'] for x in item['explanation'])-10)<.00001
    assert item['backtest']['mae']==0
    assert item['backtest']['samples']==6
    assert result['forecast_start']=='2026-09-23T12:30:00Z'


def test_incomplete_and_future_buckets_excluded():
    original=rows()
    dirty=original+[SimpleNamespace(timestamp=NOW,vehicle_count=999,average_speed=999,queue_length=999),
        SimpleNamespace(timestamp=NOW+timedelta(minutes=5),vehicle_count=999,average_speed=999,queue_length=999)]
    assert build_forecast(original,1,NOW)==build_forecast(dirty,1,NOW)


def test_stale_and_gapped_data_rejected():
    with pytest.raises(ValueError,match='stale'):
        build_forecast(rows(),1,NOW+timedelta(minutes=10))
    with pytest.raises(ValueError,match='six consecutive'):
        build_forecast(rows()[:-4]+rows()[-2:],1,NOW)


def test_api_auth_and_insufficient_data(client):
    client.app.include_router(router)
    assert client.get('/predictions/lanes/1').status_code==503
    assert client.get('/predictions/lanes/0').status_code==422
    client.app.dependency_overrides.clear()
    assert client.get('/predictions/lanes/1').status_code==401
