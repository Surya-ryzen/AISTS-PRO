import numpy as np
import pytest
from backend.app.services.roi.service import ROIService
from backend.app.services.tracking.models import Track


def track(key, x, y, width=80):
    return Track(
        key, 2, "car", 0.95, int(x - width / 2), int(y - 50), int(x + width / 2), int(y)
    )


def test_motion_selects_near_carriageway_and_rejects_opposite():
    roi = ROIService()
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    for frame in range(60):
        tracks = [
            track(i, x, 120 + frame * 8) for i, x in enumerate([200, 330, 460, 590])
        ]
        tracks += [
            track(i + 10, x, 650 - frame * 5, 20)
            for i, x in enumerate([900, 1000, 1100, 1200])
        ]
        roi.update(image, tracks)
    assert roi.ready
    assert roi.direction[1] > 0.9
    assert not roi.contains(1000, 450)
    assert roi.contains(350, 400)
    assert not any(t.track_id >= 10 for t in roi.filter_tracks(tracks))


def test_no_motion_does_not_invent_a_road():
    roi = ROIService()
    for _ in range(80):
        assert (
            roi.update(
                np.zeros((720, 1280, 3), dtype=np.uint8),
                [track(i, 200 + i * 100, 450) for i in range(5)],
            )
            == []
        )
    assert not roi.ready


def test_reviewed_profile_scales_and_assigns_real_polygons(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    roi = ROIService()
    roi.profile = {
        "polygon": [[0, 0], [0.6, 0], [0.6, 1], [0, 1]],
        "lanes": [
            [[0, 0], [0.3, 0], [0.3, 1], [0, 1]],
            [[0.3, 0], [0.6, 0], [0.6, 1], [0.3, 1]],
        ],
    }
    a, b, c = track(1, 100, 200), track(2, 400, 200), track(3, 900, 200)
    assert roi.update(np.zeros((500, 1000, 3), dtype=np.uint8), [a, b, c]) == [a, b]
    roi.assign_lane(a)
    roi.assign_lane(b)
    assert (a.lane_id, b.lane_id) == (1, 2)
    assert roi.lane_count == 2
    roi.reset("another-video")
    assert not roi.ready and not roi.manual_lanes


def test_counting_line_stays_inside_region():
    roi = ROIService()
    roi.ready = True
    roi.roi.points = [(100, 100), (500, 100), (700, 600), (0, 600)]
    a, b = roi.counting_line()
    assert roi.contains(a[0] + 1, a[1]) and roi.contains(b[0] - 1, b[1])


def test_reverse_vehicle_is_rejected_inside_hull():
    roi = ROIService()
    roi.shape = (720, 1280)
    roi.ready = True
    roi.roi.points = [(0, 0), (1200, 0), (1200, 700), (0, 700)]
    roi.direction = np.array([0, 1])
    roi.histories[1] = [(500, 500 - i * 10, 100) for i in range(10)]
    assert roi.filter_tracks([track(1, 500, 400)]) == []

def test_counting_line_accepts_both_directions():
    from backend.app.services.behavior.service import BehaviorService
    behavior = BehaviorService(-1, 300)
    behavior.update(track(1, 300, 400))
    assert behavior.update(track(1, 300, 200))['counting_line_crossed']
    assert not behavior.update(track(1, 300, 400))['counting_line_crossed']


def test_layout_save_validation(tmp_path, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from fastapi import HTTPException
    from backend.app.api import road_setup
    monkeypatch.setattr(road_setup, 'PROFILE_PATH', tmp_path / 'profiles.local')
    fake = SimpleNamespace(roi=SimpleNamespace(source='clip'), pending_roi=None)
    monkeypatch.setattr(road_setup, 'system', fake)
    polygon = [[0,0],[0.5,0],[0.5,1],[0,1]]
    data = {'source':'clip','polygon':polygon,'lanes':[polygon]}
    class Request:
        client=SimpleNamespace(host='127.0.0.1')
        headers={'origin':'http://127.0.0.1:8000','content-type':'application/json'}
        base_url='http://127.0.0.1:8000/'
        async def json(self): return data
    assert asyncio.run(road_setup.save(Request())) == {'saved':True}
    assert fake.pending_roi
    data['lanes']=[polygon,polygon]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(road_setup.save(Request()))
    assert exc.value.status_code == 400
    data['lanes']=[[[0.4,0],[0.8,0],[0.8,1],[0.4,1]]]
    with pytest.raises(HTTPException):
        asyncio.run(road_setup.save(Request()))

def test_road_only_profile_excludes_other_side_without_forcing_lanes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    roi = ROIService()
    roi.profile = {'polygon': [[0,0],[0.6,0],[0.6,1],[0,1]], 'lanes': []}
    inside, outside = track(1,300,300), track(2,900,300)
    kept = roi.update(np.zeros((720,1280,3), dtype=np.uint8), [inside,outside])
    assert kept == [inside]
    roi.assign_lane(inside)
    assert inside.lane_id is None
    assert roi.ready


def test_saved_road_profile_reloads_for_same_source(tmp_path, monkeypatch):
    import yaml
    monkeypatch.chdir(tmp_path)
    (tmp_path/'configs').mkdir()
    profile = {'polygon':[[0,0],[0.6,0],[0.6,1],[0,1]],'lanes':[]}
    (tmp_path/'configs'/'roi-profiles.local').write_text(yaml.safe_dump({'rear':profile}))
    roi=ROIService();roi.reset('rear')
    assert roi.profile == profile
    roi.reset('front')
    assert roi.profile is None


def test_remove_road_persists_and_can_be_redrawn(tmp_path, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from backend.app.api import road_setup
    monkeypatch.chdir(tmp_path)
    (tmp_path/'configs').mkdir()
    monkeypatch.setattr(road_setup, 'PROFILE_PATH', tmp_path/'configs/roi-profiles.local')
    fake=SimpleNamespace(roi=SimpleNamespace(source='clip'),pending_roi=None)
    monkeypatch.setattr(road_setup,'system',fake)
    data={'source':'clip','polygon':[],'lanes':[]}
    class Request:
        client=SimpleNamespace(host='127.0.0.1')
        headers={'origin':'http://127.0.0.1:8000','content-type':'application/json'}
        base_url='http://127.0.0.1:8000/'
        async def json(self): return data
    asyncio.run(road_setup.save(Request()))
    roi=ROIService();roi.reset('clip')
    assert roi.update(np.zeros((100,100,3),dtype=np.uint8),[]) == []
    assert not roi.ready and roi.profile['disabled']
    data['polygon']=[[0,0],[1,0],[1,1],[0,1]]
    data['lanes']=[[[0,0],[.5,0],[.5,1],[0,1]]]
    asyncio.run(road_setup.save(Request()))
    roi.reset('clip');roi.update(np.zeros((100,100,3),dtype=np.uint8),[])
    assert roi.ready and len(roi.manual_lanes)==1
    data['lanes']=[]
    asyncio.run(road_setup.save(Request()))
    roi.reset('clip');roi.update(np.zeros((100,100,3),dtype=np.uint8),[])
    assert roi.ready and not roi.manual_lanes
