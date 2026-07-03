from ultralytics import YOLO

def main():

    model = YOLO(
        r"C:\Users\Kiki Salikil\Downloads\capstone-cuda\runs\detect\runs\car_color_detector-3\weights\best.pt"
    )

    model.train(
        data=r"C:\Users\Kiki Salikil\Downloads\capstone-cuda\data.yaml",
        epochs=50,
        imgsz=416,
        batch=2,
        workers=0,
        device=0,
        project="runs",
        name="car_color_detector_v4"
    )

if __name__ == "__main__":
    main()