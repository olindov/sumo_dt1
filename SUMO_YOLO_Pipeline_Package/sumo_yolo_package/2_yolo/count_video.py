import argparse
import csv
from pathlib import Path

import cv2
from ultralytics import YOLO


COCO_NAMES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


ALLOWED_CLASSES = {1, 2, 3, 5, 7}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLO tracking on a traffic video and export tracked objects to CSV.")
    parser.add_argument("--video", required=True, help="Path to input video")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO model path or model name")
    parser.add_argument("--output_csv", required=True, help="CSV file for tracked detections")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=1280, help="Inference image size")
    parser.add_argument("--tracker", default="bytetrack.yaml", help="Ultralytics tracker config")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video_path = Path(args.video)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()

    model = YOLO(args.model)

    results = model.track(
        source=str(video_path),
        conf=args.conf,
        imgsz=args.imgsz,
        tracker=args.tracker,
        persist=True,
        stream=True,
        verbose=False,
    )

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "frame",
            "timestamp_s",
            "track_id",
            "class_id",
            "class_name",
            "x1",
            "y1",
            "x2",
            "y2",
            "cx",
            "cy",
            "width",
            "height",
        ])

        frame_idx = 0
        for result in results:
            boxes = result.boxes
            if boxes is None or boxes.id is None:
                frame_idx += 1
                continue

            ids = boxes.id.int().cpu().tolist()
            xyxy = boxes.xyxy.cpu().tolist()
            classes = boxes.cls.int().cpu().tolist()

            for track_id, box, class_id in zip(ids, xyxy, classes):
                if class_id not in ALLOWED_CLASSES:
                    continue

                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                cx = x1 + w / 2
                cy = y1 + h / 2
                timestamp_s = frame_idx / fps
                writer.writerow([
                    frame_idx,
                    round(timestamp_s, 3),
                    track_id,
                    class_id,
                    COCO_NAMES.get(class_id, str(class_id)),
                    round(x1, 2),
                    round(y1, 2),
                    round(x2, 2),
                    round(y2, 2),
                    round(cx, 2),
                    round(cy, 2),
                    round(w, 2),
                    round(h, 2),
                ])
            frame_idx += 1

    print(f"Saved tracked detections to: {output_csv}")


if __name__ == "__main__":
    main()
