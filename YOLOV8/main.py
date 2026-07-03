from ultralytics import YOLO


def main():
    model = YOLO("yolov8n.pt")

    model.train(
        data="data.yaml",
        epochs=100,
        imgsz=416,
        batch=2,
        workers=0,
        device=0,
        project="runs",
        name="car_color_detector"
    )

    print("Training completed!")

    model.export(format="onnx")

    print("Model exported.")


if __name__ == "__main__":
    main()