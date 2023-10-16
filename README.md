# rtw-locate-settlements

Python script to get the names and in-game coordinates of settlements in _Rome: Total War_.

Please note that this script is not thoroughly tested and makes certain assumptions. For example, it only looks inside `data/world/maps/base` for `map_regions.tga` and `descr_regions.txt`. It does not look through campaign folders.

## Usage

Open a command prompt and run one of the following commands:

- To list settlement names, coordinates, and colors:
  - `python rtw-locate-settlements.py mod_path`
  - `mod_path` is the path to the mod folder itself, not `data` or any other subfolders.
- To read map_regions.tga and list coordinates and colors only:
  - `python rtw-locate-settlements.py map_regions_path`
  - `map_regions_path` is the path to `map_regions.tga`
  - in this mode, invalidly placed settlements will be listed in `invalid_settlements.csv`

The script will save results to `settlements.csv`.

Brought to you by the EB Online Team
