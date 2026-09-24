from backend.app.system import system
from backend.app.services.system.service import TrafficSystemService


def get_system() -> TrafficSystemService:
    """
    Return the shared Traffic System instance.
    """

    return system
