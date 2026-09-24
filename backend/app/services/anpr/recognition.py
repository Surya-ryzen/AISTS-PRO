"""CPU OCR prototype. Plate candidates and emergency text require review."""
import re
import threading
import numpy as np

PLATE = re.compile(r'(?:[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}|[0-9]{2}BH[0-9]{4}[A-Z]{1,2})')


def normalize_plate(text):
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def valid_plate(text):
    return bool(PLATE.fullmatch(normalize_plate(text)))


def extract_candidates(results):
    """No O/0 substitution: preserve uncertain reads instead of inventing plates."""
    plates, emergencies = {}, []
    for box, raw, confidence in results or []:
        value = normalize_plate(raw)
        confidence = float(confidence)
        if confidence < .65:
            continue
        if valid_plate(value):
            item = dict(plate=value, raw_text=raw[:100], confidence=confidence,
                        bbox=np.asarray(box).astype(float).tolist())
            if value not in plates or confidence > plates[value]['confidence']:
                plates[value] = item
        words = re.sub(r'[^A-Z ]', ' ', raw.upper()).split()
        kind = 'ambulance' if ('AMBULANCE' in words or 'ECNALUBMA' in words) else None
        if 'FIRE' in words and ('RESCUE' in words or 'BRIGADE' in words or 'SERVICE' in words or 'SERVICES' in words):
            kind = 'fire_engine'
        if 'POLICE' in words:
            kind = 'police'
        if kind:
            emergencies.append(dict(vehicle_type=kind, confidence=confidence,
                                    evidence=f'Visible text: {raw[:200]}'))
    return list(plates.values()), emergencies


class RecognitionService:
    def __init__(self):
        self.reader = None
        self.lock = threading.Lock()

    def recognize(self, image, include_detector=True):
        with self.lock:
            if self.reader is None:
                try:
                    from rapidocr_onnxruntime import RapidOCR
                    self.reader = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
                except ImportError as exc:
                    raise RuntimeError('Install backend/requirements/week10.txt to enable OCR.') from exc
            results, _ = self.reader(image)
            plates, candidates = extract_candidates(results)
            from .emergency import detector
            if include_detector:
                candidates.extend(detector.detect(image))
            return plates, candidates


recognizer = RecognitionService()
