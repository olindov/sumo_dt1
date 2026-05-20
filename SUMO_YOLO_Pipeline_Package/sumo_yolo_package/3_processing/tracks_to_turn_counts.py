import argparse
from pathlib import Path

import pandas as pd


VEHICLE_MAP = {
    "car": "passenger",
    "bus": "bus",
    "truck": "truck",
    "motorcycle": "motorcycle",
    "bicycle": "bicycle",
}


def infer_zone(cx: float, cy: float, width: float, height: float) -> str:
    """Placeholder heuristic.
    Replace with polygon-based entry/exit zone mapping for a real project.
    """
    if cy < height * 0.25:
        return "north"
    if cy > height * 0.75:
        return "south"
    if cx < width * 0.25:
        return "west"
    if cx > width * 0.75:
        return "east"
    return "center"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert tracked YOLO detections to turn-count CSV.")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--interval_minutes", type=int, default=15)
    parser.add_argument("--frame_width", type=float, default=1920)
    parser.add_argument("--frame_height", type=float, default=1080)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    if df.empty:
        raise ValueError("Input CSV is empty.")

    grouped_rows = []

    for track_id, g in df.groupby("track_id"):
        g = g.sort_values("timestamp_s")
        first = g.iloc[0]
        last = g.iloc[-1]

        entry = infer_zone(first["cx"], first["cy"], args.frame_width, args.frame_height)
        exit_ = infer_zone(last["cx"], last["cy"], args.frame_width, args.frame_height)

        if entry == exit_ or "center" in {entry, exit_}:
            continue

        interval_s = args.interval_minutes * 60
        begin = int(first["timestamp_s"] // interval_s) * interval_s
        end = begin + interval_s

        vehicle_type = VEHICLE_MAP.get(str(first["class_name"]).lower(), "passenger")

        grouped_rows.append(
            {
                "begin": begin,
                "end": end,
                "from_edge": f"in_{entry}",
                "to_edge": f"out_{exit_}",
                "vehicle_type": vehicle_type,
                "count": 1,
                "track_id": track_id,
            }
        )

    out = pd.DataFrame(grouped_rows)
    if out.empty:
        raise ValueError(
            "No turning movements were inferred. Review zone logic or tracking quality."
        )

    out = (
        out.groupby(["begin", "end", "from_edge", "to_edge", "vehicle_type"], as_index=False)["count"]
        .sum()
        .sort_values(["begin", "from_edge", "to_edge", "vehicle_type"])
    )

    out.to_csv(output_csv, index=False)
    print(f"Saved turn counts to: {output_csv}")


if __name__ == "__main__":
    main()
