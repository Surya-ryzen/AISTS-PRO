"""Local calibration UI. Mutations require a same-origin JSON request on loopback."""

import json
from pathlib import Path

import cv2
import numpy as np
import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from backend.app.system import system

router = APIRouter(tags=["Road and lane setup"])
PROFILE_PATH = Path("configs/roi-profiles.local")


def local_only(request):
    if not request.client or request.client.host not in ("127.0.0.1", "::1"):
        raise HTTPException(403, "Road setup is available only on this computer.")


@router.get("/road-setup", response_class=HTMLResponse)
def page(request: Request):
    local_only(request)
    return Path(__file__).with_name("road_setup.html").read_text(encoding="utf-8")


@router.get("/road-setup/frame")
def frame(request: Request):
    local_only(request)
    result = system.get_latest_result()
    if result is None:
        raise HTTPException(503, "Waiting for first frame")
    ok, encoded = cv2.imencode(".jpg", result.frame.image)
    if not ok:
        raise HTTPException(503, "Frame encoding failed")
    return Response(
        encoded.tobytes(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/road-setup/state")
def state(request: Request):
    local_only(request)
    roi = system.roi
    h, w = roi.shape or (720, 1280)
    normalize = lambda points: [[x / (w - 1), y / (h - 1)] for x, y in points]
    return dict(
        source=roi.source,
        status=roi.status,
        ready=roi.ready,
        polygon=normalize(roi.roi.points),
        lanes=[normalize(p) for p in roi.manual_lanes],
        estimated_lane_count=roi.lane_count,
        reviewed=bool(roi.profile),
    )


def validate_polygon(points):
    if not isinstance(points, list) or not 3 <= len(points) <= 32:
        raise HTTPException(400, "Use 3 to 32 corners per polygon.")
    try:
        arr = np.asarray(points, dtype=np.float32)
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid polygon coordinates.")
    if (
        arr.shape != (len(points), 2)
        or not np.isfinite(arr).all()
        or (arr < 0).any()
        or (arr > 1).any()
    ):
        raise HTTPException(400, "Corners must be inside the image.")
    if not cv2.isContourConvex(arr) or cv2.contourArea(arr) < 0.001:
        raise HTTPException(
            400, "Draw a convex polygon with corners in order, without crossing edges."
        )
    return arr


@router.post("/road-setup/save")
async def save(request: Request):
    local_only(request)
    if request.headers.get("origin") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Use the road setup page on this server.")
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "JSON required")
    try:
        data = await request.json()
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid JSON")
    if not isinstance(data, dict) or data.get("source") != system.roi.source:
        raise HTTPException(409, "Video changed. Reload the page.")
    road_removed = data.get("polygon") == []
    polygon = None if road_removed else validate_polygon(data.get("polygon"))
    lanes = data.get("lanes")
    if not isinstance(lanes, list) or not 0 <= len(lanes) <= 8:
        raise HTTPException(400, "Use up to 8 lane polygons, or save only the road to estimate traffic bands.")
    if road_removed and lanes:
        raise HTTPException(400, "Remove lanes before removing the road.")
    checked = []
    for lane in lanes:
        arr = validate_polygon(lane)
        if any(
            cv2.pointPolygonTest(polygon, tuple(map(float, p)), True) < -0.001
            for p in arr
        ):
            raise HTTPException(400, "Every lane must stay inside the road region.")
        if any(cv2.intersectConvexConvex(arr, other)[0] > 0.0001 for other in checked):
            raise HTTPException(400, "Lane interiors must not overlap.")
        checked.append(arr)
    profiles = yaml.safe_load(PROFILE_PATH.read_text()) if PROFILE_PATH.exists() else {}
    profiles = profiles or {}
    profiles[data["source"]] = {"polygon": data["polygon"], "lanes": lanes, "disabled": road_removed}
    temp = PROFILE_PATH.with_suffix(".tmp")
    temp.write_text(yaml.safe_dump(profiles))
    temp.replace(PROFILE_PATH)
    system.pending_roi = True
    return {"saved": True}
