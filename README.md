# rtw-locate-settlements

Python script to get the names and in-game coordinates of settlements in _Rome: Total War_.

Please note that this script is not thoroughly tested and makes certain assumptions. For example, it only looks inside `data/world/maps/base` for `map_regions.tga` and `descr_regions.txt`. It does not look through campaign folders.

## Usage

Open a command prompt and run the following command:

`python rtw-locate-settlements.py modpath`

`modpath` is the path to the mod folder itself, not `data` or any other subfolders.

The script will save settlement coordinates and names to `settlements.txt`.

Brought to you by the EB Online Team
