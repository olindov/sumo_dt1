import os
import time
import json
import math
import hashlib
from typing import Dict, Any, List, Tuple, Optional

import requests

# ----------------------------
# CONFIG (edit this)
# ----------------------------

API_KEY = "iW1BL4I14DAtwktNcsIpUF5K1w76Hohv"

# Sarajevo (approx) bounding box: (min_lon, min_lat, max_lon, max_lat)
# Adjust if you want smaller/larger coverage.
SARAJEVO_BBOX = (18.30, 43.80, 18.50, 43.95)

# Sampling grid step in degrees.
# ~0.003 deg lat ≈ 333m; start with 0.004-0.006 to avoid too many calls.
GRID_STEP_DEG = 0.005

# Zoom level for flowSegmentData (affects which roads you get)
# Higher zoom => more local roads but more calls/duplicates. Start with 10-12.
ZOOM = 11

# Rate limiting (seconds between API calls)
SLEEP_SEC = 0.12

# Output
OUT_GEOJSON = "sarajevo_tomtom_flow_segments.geojson"
OUT_NDJSON = "sarajevo_tomtom_raw.ndjson"  # raw responses per point (optional)

# ----------------------------
# TomTom endpoint
# ----------------------------
FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/{zoom}/json"

# ----------------------------
# Helpers
# ----------------------------

def frange(a: float, b: float, step: float):
    x = a
    while x <= b + 1e-12:
        yield x
        x += step

def safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def segment_geometry(resp: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
    """
    Returns list of (lon, lat) points for the segment geometry.
    TomTom returns coordinates as list of {latitude, longitude}.
    """
    coords = safe_get(resp, ["flowSegmentData", "coordinates", "coordinate"])
    if not coords or not isinstance(coords, list):
        return None
    out = []
    for p in coords:
        lat = p.get("latitude")
        lon = p.get("longitude")
        if lat is None or lon is None:
            continue
        out.append((lon, lat))
    return out if len(out) >= 2 else None

def geometry_hash(points: List[Tuple[float, float]]) -> str:
    """
    Hash geometry to deduplicate segments.
    Rounds coords a bit to reduce near-duplicates.
    """
    rounded = [(round(lon, 6), round(lat, 6)) for lon, lat in points]
    s = json.dumps(rounded, separators=(",", ":"), ensure_ascii=False)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def fetch_flow(lat: float, lon: float, zoom: int) -> Optional[Dict[str, Any]]:
    url = FLOW_URL.format(zoom=zoom)
    params = {
        "point": f"{lat},{lon}",
        "key": API_KEY,
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 429:
            # Too many requests - backoff
            time.sleep(1.5)
            return None
        if r.status_code != 200:
            return None
        return r.json()
    except requests.RequestException:
        return None

def to_feature(points: List[Tuple[float, float]], props: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": points,  # (lon, lat)
        },
        "properties": props,
    }

def main():

    min_lon, min_lat, max_lon, max_lat = SARAJEVO_BBOX

    # generate grid points
    points = []
    for lat in frange(min_lat, max_lat, GRID_STEP_DEG):
        for lon in frange(min_lon, max_lon, GRID_STEP_DEG):
            points.append((lat, lon))

    print(f"Grid points: {len(points)}  | bbox={SARAJEVO_BBOX} step={GRID_STEP_DEG}")

    seen = set()
    features = []
    kept = 0
    calls = 0

    # raw log
    raw_f = open(OUT_NDJSON, "w", encoding="utf-8")

    for i, (lat, lon) in enumerate(points, start=1):
        resp = fetch_flow(lat, lon, ZOOM)
        calls += 1
        time.sleep(SLEEP_SEC)

        if resp is None:
            continue

        # save raw response (optional)
        raw_f.write(json.dumps({"query": {"lat": lat, "lon": lon}, "resp": resp}, ensure_ascii=False) + "\n")

        geom = segment_geometry(resp)
        if geom is None:
            continue

        h = geometry_hash(geom)
        if h in seen:
            continue
        seen.add(h)

        fsd = resp.get("flowSegmentData", {})

        props = {
            "source": "TomTom Traffic Flow",
            "query_lat": lat,
            "query_lon": lon,
            "zoom": ZOOM,
            "frc": fsd.get("frc"),  # functional road class
            "currentSpeed": fsd.get("currentSpeed"),
            "freeFlowSpeed": fsd.get("freeFlowSpeed"),
            "currentTravelTime": fsd.get("currentTravelTime"),
            "freeFlowTravelTime": fsd.get("freeFlowTravelTime"),
            "confidence": fsd.get("confidence"),
            "roadClosure": fsd.get("roadClosure"),
            "jamFactor": fsd.get("jamFactor"),
        }

        # some responses include "openlr" (useful as an id if present)
        openlr = fsd.get("openlr")
        if openlr:
            props["openlr"] = openlr

        features.append(to_feature(geom, props))
        kept += 1

        if kept % 50 == 0:
            print(f"[{i}/{len(points)}] calls={calls} unique_segments={kept}")

    raw_f.close()

    geojson = {"type": "FeatureCollection", "features": features}
    with open(OUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    print(f"\nDone ✅ unique_segments={kept}")
    print(f"Saved: {OUT_GEOJSON}")
    print(f"Raw log: {OUT_NDJSON}")

if __name__ == "__main__":
    main()
