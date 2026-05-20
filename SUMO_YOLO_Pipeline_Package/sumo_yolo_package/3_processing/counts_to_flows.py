import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def indent(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert count CSV to SUMO flows.xml")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_xml", required=True)
    parser.add_argument("--depart_lane", default="best")
    parser.add_argument("--depart_speed", default="max")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_xml = Path(args.output_xml)
    output_xml.parent.mkdir(parents=True, exist_ok=True)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    required = {"begin", "end", "from_edge", "to_edge", "vehicle_type", "count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    routes = ET.Element("routes")

    vtypes = {
        "passenger": {"accel": "2.6", "decel": "4.5", "length": "5.0", "maxSpeed": "13.9", "guiShape": "passenger"},
        "bus": {"accel": "1.2", "decel": "4.0", "length": "12.0", "maxSpeed": "11.0", "guiShape": "bus"},
        "truck": {"accel": "1.0", "decel": "4.0", "length": "8.0", "maxSpeed": "11.0", "guiShape": "truck"},
        "motorcycle": {"accel": "3.0", "decel": "4.5", "length": "2.2", "maxSpeed": "16.7", "guiShape": "motorcycle"},
        "bicycle": {"accel": "1.2", "decel": "3.0", "length": "1.8", "maxSpeed": "5.5", "guiShape": "bicycle"},
    }

    for vt, attrs in vtypes.items():
        ET.SubElement(routes, "vType", id=vt, **attrs)

    for idx, row in df.iterrows():
        ET.SubElement(
            routes,
            "flow",
            id=f"flow_{idx+1}",
            begin=str(int(row["begin"])),
            end=str(int(row["end"])),
            number=str(int(row["count"])),
            from_=str(row["from_edge"]),
            to=str(row["to_edge"]),
            type=str(row["vehicle_type"]),
            departLane=args.depart_lane,
            departSpeed=args.depart_speed,
        )

    # Fix XML attribute name from_ -> from
    xml_text = ET.tostring(routes, encoding="unicode")
    xml_text = xml_text.replace("from_=", "from=")

    output_xml.write_text(xml_text, encoding="utf-8")
    print(f"Saved SUMO flows to: {output_xml}")


if __name__ == "__main__":
    main()
