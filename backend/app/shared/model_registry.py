from ultralytics import YOLO


class ModelRegistry:
    """
    Stores shared AI models.
    """

    _models = {}

    @classmethod
    def get_yolo(cls, model_path: str):

        if model_path not in cls._models:

            cls._models[model_path] = YOLO(model_path)

        return cls._models[model_path]