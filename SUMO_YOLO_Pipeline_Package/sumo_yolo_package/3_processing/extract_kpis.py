import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract simple KPIs from SUMO tripinfo.xml")
    parser.add_argument("--tripinfo", required=True)
    parser.add_argument("--output_csv", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tripinfo_path = Path(args.tripinfo)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not tripinfo_path.exists():
        raise FileNotFoundError(f"tripinfo.xml not found: {tripinfo_path}")

    root = ET.parse(tripinfo_path).getroot()
    rows = []
    for trip in root.findall("tripinfo"):
        rows.append(
            {
                "id": trip.attrib.get("id"),
                "depart": float(trip.attrib.get("depart", 0)),
                "arrival": float(trip.attrib.get("arrival", 0)),
                "duration": float(trip.attrib.get("duration", 0)),
                "routeLength": float(trip.attrib.get("routeLength", 0)),
                "waitingTime": float(trip.attrib.get("waitingTime", 0)),
                "timeLoss": float(trip.attrib.get("timeLoss", 0)),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No tripinfo rows found.")

    summary = pd.DataFrame(
        [
            {
                "vehicles": len(df),
                "avg_duration_s": round(df["duration"].mean(), 2),
                "avg_waiting_s": round(df["waitingTime"].mean(), 2),
                "avg_timeloss_s": round(df["timeLoss"].mean(), 2),
                "avg_route_m": round(df["routeLength"].mean(), 2),
            }
        ]
    )
    summary.to_csv(output_csv, index=False)
    print(f"Saved KPI summary to: {output_csv}")


if __name__ == "__main__":
    main()
