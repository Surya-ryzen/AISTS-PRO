from backend.app.services.detection.model_loader import ModelLoader


def main():

    loader = ModelLoader()

    model = loader.load()

    print("=" * 50)
    print("YOLO loaded successfully")
    print(model)
    print("=" * 50)


if __name__ == "__main__":
    main()