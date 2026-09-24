from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from backend.app.api.decision import decision

def test_no_decision_has_explicit_unavailable_response():
    with pytest.raises(HTTPException) as exc:
        decision(SimpleNamespace(decision=SimpleNamespace(last_decision=None)), None)
    assert exc.value.status_code == 503

def test_available_decision_keeps_fields():
    latest=SimpleNamespace(selected_lane=2,green_time=30,reason="Medium Queue")
    result=decision(SimpleNamespace(decision=SimpleNamespace(last_decision=latest)),None)
    assert result.selected_lane==2 and result.green_time==30
