# SUMO + YOLO Pipeline Package

This package is a **ready-to-adapt starter pipeline** for building a traffic Digital Twin workflow:

**Video / camera input -> YOLO detection + tracking -> turn/count CSV -> SUMO flows -> simulation -> KPI outputs**

It is designed for Sarajevo / East Sarajevo style pilot deployments, but it is intentionally generic so you can adapt it to any junction or corridor.

## What is included

- YOLO-based video processing scripts
- CSV templates for counts and OD/turning flows
- Scripts that convert counts into SUMO-ready XML
- SUMO configuration templates
- Detector definitions template
- KPI export template
- Methodology and deployment notes

## What is NOT fully site-specific yet

Because this package was generated without your final camera geometry, junction IDs, and calibrated field data, the following still require your local project data:

- `4_sumo/network/network.net.xml`
- exact lane-to-lane turning mappings
- calibrated route definitions
- final detector positions
- final signal plans / TLS logic

## Recommended workflow

1. Build or export the road network in SUMO / netedit / osmWebWizard.
2. Put your input video in `1_input/video/`.
3. Run YOLO counting.
4. Review and clean the generated CSV counts.
5. Convert counts to SUMO flows.
6. Run SUMO simulation.
7. Compare observed vs simulated values.
8. Adjust parameters and re-run.

## Quick start

### 1) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2) Install SUMO
- Install SUMO and add it to system PATH.
- Confirm with:

```bash
sumo --version
```

### 3) Run YOLO on a video

```bash
python 2_yolo/count_video.py \
  --video "1_input/video/sample.mp4" \
  --model yolov8n.pt \
  --output_csv "1_input/counts/raw_tracks.csv"
```

### 4) Convert tracks to turn counts

```bash
python 3_processing/tracks_to_turn_counts.py \
  --input_csv "1_input/counts/raw_tracks.csv" \
  --output_csv "1_input/counts/turn_counts_15min.csv"
```

### 5) Convert counts to SUMO flows

```bash
python 3_processing/counts_to_flows.py \
  --input_csv "1_input/counts/turn_counts_15min.csv" \
  --output_xml "4_sumo/demand/flows.xml"
```

### 6) Run SUMO

```bash
sumo-gui -c 4_sumo/config/scenario.sumocfg
```

## Folder structure

- `config/` project settings
- `docs/` methodology and deployment notes
- `1_input/` video and intermediate count files
- `2_yolo/` YOLO processing scripts
- `3_processing/` flow conversion logic
- `4_sumo/` SUMO templates and config
- `5_dashboard/` KPI templates
- `sample_data/` starter example files

## Recommended next customization for your project

- replace placeholder detector coordinates
- replace placeholder edge IDs with your real SUMO edge IDs
- calibrate turning movements for Sarajevo pilot junctions
- add emission output and queue length outputs
- connect the results to a dashboard or Power BI
