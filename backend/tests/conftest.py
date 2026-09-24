"""Isolated configuration before application imports during test collection."""
import os
from pathlib import Path
for key, value in dict(APP_NAME='test', APP_ENV='test', DEBUG='false', SECRET_KEY='test-only-not-for-deployment', API_HOST='127.0.0.1', API_PORT='8001', DATABASE_URL='sqlite://', LOG_LEVEL='INFO', MODEL_PATH='yolov8s.pt', ALLOWED_ORIGINS='http://localhost', PROJECT_NAME='test', VERSION='test').items():
    os.environ[key] = value
os.environ['YOLO_CONFIG_DIR'] = str(Path(__file__).resolve().parents[2] / 'Ultralytics')
