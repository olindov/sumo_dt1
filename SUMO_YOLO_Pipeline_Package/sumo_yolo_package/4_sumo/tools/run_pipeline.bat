@echo off
REM Windows helper script
python ..\..\2_yolo\count_video.py --video ..\..\1_input\video\sample.mp4 --model yolov8n.pt --output_csv ..\..\1_input\counts\raw_tracks.csv
python ..\..\3_processing\tracks_to_turn_counts.py --input_csv ..\..\1_input\counts\raw_tracks.csv --output_csv ..\..\1_input\counts\turn_counts_15min.csv
python ..\..\3_processing\counts_to_flows.py --input_csv ..\..\1_input\counts\turn_counts_15min.csv --output_xml ..\demand\flows.xml
sumo-gui -c ..\config\scenario.sumocfg
