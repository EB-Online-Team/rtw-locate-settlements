#!/usr/bin/env python3

"""Saves a list of settlements and their coordinates.

Usage:
    python rtw-locate-settlements.py modpath

MIT License

Copyright (c) 2023 Vartan Haghverdi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image

RE_REGION = re.compile(
    r"^([\w-]+)\s+?(?:legion:\s*(\w+)\s*)?([\w-]+)\s+?(\w+)\s+?([\w-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)\s*(\d+)\s*(\d+)\s*((?:\w+[ \t]+\d+[ \t]*)+)?",
    re.M,
)
RE_RELIGION = re.compile(r"(?:(\w+)[ \t]+(\d+))")


def parse_descr_regions(path_to_descr_regions: Path):
    with open(path_to_descr_regions) as f:
        regions = []

        for (
            province,
            legion,
            settlement,
            faction,
            rebel,
            r,
            g,
            b,
            resources,
            triumph,
            farm,
            religion,
        ) in RE_REGION.findall(f.read()):
            r, g, b = int(r), int(g), int(b)
            resources = [r.strip() for r in resources.split(",")]
            triumph, farm = int(triumph), int(farm)
            religion = {
                name: int(value) for name, value in RE_RELIGION.findall(religion)
            }
            regions.append(
                {
                    "province": province,
                    "legion": legion,
                    "settlement": settlement,
                    "faction": faction,
                    "rebel": rebel,
                    "color": (r, g, b),
                    "resources": resources,
                    "triumph": triumph,
                    "farm": farm,
                    "religion": religion,
                }
            )

        return regions


def locate_settlements(path_to_map_regions: Path, path_to_descr_regions: Path):
    regions = parse_descr_regions(path_to_descr_regions)
    regions_by_color = {region["color"]: region["settlement"] for region in regions}
    settlements = dict()

    with Image.open(path_to_map_regions) as im:
        for i, pixel in enumerate(im.getdata()):
            # only if pixel is black (settlement)
            if pixel == (0, 0, 0):
                x = i % im.width
                y = i // im.width

                # get pixels west, east, north, and south of settlement
                pixel_left = im.getpixel((x - 1, y)) if x > 0 else None
                pixel_right = im.getpixel((x + 1, y)) if x < im.width - 1 else None
                pixel_up = im.getpixel((x, y - 1)) if y > 0 else None
                pixel_down = im.getpixel((x, y + 1)) if y < im.height - 1 else None
                surrounding_pixels = set(
                    [pixel_left, pixel_right, pixel_up, pixel_down]
                )

                color = regions_by_color.keys() & surrounding_pixels
                if not color:
                    print(
                        f"Could not determine region corresponding to settlement at {x}, {y}."
                    )
                    exit(1)
                color = list(color)[0]
                name = regions_by_color[color]
                y = im.height - y - 1
                settlements[name] = (x, y)

    return settlements


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n\tpython rtw-locate-settlements.py modpath")
        exit()

    path_to_mod = Path(sys.argv[1])
    path_to_base = path_to_mod / "data" / "world" / "maps" / "base"
    path_to_map_regions = path_to_base / "map_regions.tga"
    path_to_descr_regions = path_to_base / "descr_regions.txt"

    if not path_to_mod.is_dir():
        print("Invalid mod directory.", file=sys.stderr)
        exit(1)
    if not path_to_base.is_dir():
        print("Missing data/world/maps/base directory.", file=sys.stderr)
        exit(1)
    if not path_to_map_regions.is_file():
        print("Missing map_regions.tga.", file=sys.stderr)
        exit(1)
    if not path_to_descr_regions.is_file():
        print("Missing descr_regions.txt.", file=sys.stderr)
        exit(1)

    settlements = locate_settlements(path_to_map_regions, path_to_descr_regions)
    with open("settlements.txt", "w") as f:
        for name, location in settlements.items():
            x, y = location
            f.write(f"{x:4}  {y:4}\t{name}\n")
