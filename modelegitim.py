from ultralytics import YOLO



if __name__ == "__main__":
    model = YOLO("yolov12m.pt")
    model.train(
        data="/home/comp1/Desktop/datasett3/data.yaml",
        epochs=100,
        imgsz=960,
        batch=8,
        device=0,
        workers=8,
    )
