# Zone definition guide

To convert tracks into turning movements, define screen-space zones such as:

- entry_north
- entry_south
- entry_east
- entry_west
- exit_north
- exit_south
- exit_east
- exit_west

You can later encode these as polygons or simple bounding rectangles.

For the starter package, the conversion script uses **simple screen quadrants** as placeholders.
Replace that logic with your real junction polygons for best accuracy.
