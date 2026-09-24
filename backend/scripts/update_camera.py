from backend.app.database.session_manager import get_db_session
from backend.app.services.persistence.service import PersistenceService


def main():

    persistence = PersistenceService()

    with get_db_session() as session:

        camera = persistence.update_camera_source(
            session=session,
            camera_id=1,
            source="datasets/videos/raw/traffic_rear.mp4",
            source_type="file",
        )

        if camera is None:
            print("Camera not found.")
            return

        print("Camera source updated successfully.")
        print(f"Source: {camera.source}")
        print(f"Source Type: {camera.source_type}")


if __name__ == "__main__":
    main()
