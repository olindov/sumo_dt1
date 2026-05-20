# Methodology: SUMO + YOLO Traffic Digital Twin Pipeline

## Objective
Create an operational workflow that converts observed traffic video into simulation-ready mobility demand for a pilot urban corridor or intersection.

## Main stages

### 1. Data acquisition
- fixed traffic cameras
- drone or mast-mounted video
- optional radar / loop / Bluetooth validation

### 2. AI-based traffic observation
- YOLO detects vehicles frame by frame
- tracker keeps object IDs over time
- trajectories are exported to CSV

### 3. Traffic movement extraction
- trajectories are mapped to entry and exit zones
- each tracked object is converted into a movement:
  - north -> east
  - east -> south
  - etc.
- counts are aggregated by 5 min / 15 min / 1 hour

### 4. SUMO demand generation
- counts are converted into `<flow>` definitions
- optional OD estimation can be added later
- routeSampler or duarouter can refine routes further

### 5. Simulation and calibration
- compare simulated counts with observed counts
- adjust demand, route choice, and TLS timings
- validate queue lengths and travel times

### 6. KPI evaluation
- traffic volume
- delay
- queue length
- emissions
- conflict hotspots
- modal split where available

## Minimum field data required
- camera location and orientation
- time period of the count
- junction movement labels
- SUMO edge IDs for entries/exits
- signal timing if signalized

## Good practice for Sarajevo pilots
- start with one intersection or one short corridor
- calibrate one peak hour first
- only then expand to full daily scenarios
