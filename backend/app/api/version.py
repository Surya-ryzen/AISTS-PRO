from fastapi import APIRouter

router = APIRouter(
    tags=["System"],
)


@router.get("/version")
def version():
    return {"project": "AI Smart Traffic System", "version": "1.0.0"}
