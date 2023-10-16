#!/usr/bin/env python3

"""Saves a list of settlements and their coordinates.

To list settlement names and coordinates:
    python rtw-locate-settlements.py mod_path

To read map_regions.tga and list coordinates and colors only:
    python rtw-locate-settlements.py map_regions_path

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
    settlements = []

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
                settlements.append(
                    {
                        "settlement": name,
                        "coordinate": (x, y),
                        "color": color,
                    }
                )

    return settlements


def is_settlement(pixel):
    return pixel == (0, 0, 0)


def is_port(pixel):
    return pixel == (255, 255, 255)


def is_sea(pixel):
    r, g, _ = pixel
    return r == 41 and g == 140


def locate_settlements_map_only(path_to_map_regions):
    settlements = []
    invalid_settlements = []

    with Image.open(path_to_map_regions) as im:
        for i, pixel in enumerate(im.getdata()):
            if is_settlement(pixel):
                # pixel coordinates
                x = i % im.width
                y = i // im.width

                # get adjacent pixels (not diagonally)
                pixel_left = im.getpixel((x - 1, y)) if x > 0 else None
                pixel_right = im.getpixel((x + 1, y)) if x < im.width - 1 else None
                pixel_above = im.getpixel((x, y - 1)) if y > 0 else None
                pixel_below = im.getpixel((x, y + 1)) if y < im.height - 1 else None
                adjacent_pixels = [pixel_left, pixel_right, pixel_above, pixel_below]

                # test if settlement is valid (at least one adjacent )
                valid_region = False
                for pixel in adjacent_pixels:
                    if not (is_port(pixel) or is_sea(pixel)):
                        valid_region = True
                        region_color = pixel
                        break

                if valid_region:
                    # invert y value to compute in-game coordinate
                    y = im.height - y - 1
                    settlements.append(
                        {
                            "coordinate": (x, y),
                            "color": region_color,
                        }
                    )
                else:
                    invalid_settlements.append((x, y))

    return settlements, invalid_settlements


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("To list settlement names and coordinates:")
        print("\tpython rtw-locate-settlements.py mod_path")
        print("To read map_regions.tga and list coordinates and colors only:")
        print("\tpython rtw-locate-settlements.py map_regions_path")
        exit()

    path_to_mod = Path(sys.argv[1])

    # if user passed in map_regions.tga
    if path_to_mod.is_file() and path_to_mod.name.lower() == "map_regions.tga":
        settlements, invalid_settlements = locate_settlements_map_only(path_to_mod)
        n = len(settlements)
        if n == 0:
            print("No settlements found.")
        else:
            f = open("settlements.csv", "w", encoding="utf-8")
            f.write("x,y,r,g,b\n")
            for settlement in settlements:
                x, y = settlement["coordinate"]
                r, g, b = settlement["color"]
                f.write(f"{x},{y},{r},{g},{b}\n")
            f.close()
            print(f"{n} settlements saved to settlements.csv")
        n = len(invalid_settlements)
        if n > 0:
            f = open("invalid_settlements.csv", "w", encoding="utf-8")
            f.write("x,y\n")
            for x, y in invalid_settlements:
                f.write(f"{x},{y}\n")
            f.close()
            print(f"{n} invalid settlements saved to invalid_settlements.csv")
        exit()

    if not path_to_mod.is_dir():
        print("Invalid mod directory.", file=sys.stderr)
        exit(1)

    path_to_base = path_to_mod / "data" / "world" / "maps" / "base"
    if not path_to_base.is_dir():
        print("Missing data/world/maps/base directory.", file=sys.stderr)
        exit(1)

    path_to_map_regions = path_to_base / "map_regions.tga"
    if not path_to_map_regions.is_file():
        print("Missing map_regions.tga.", file=sys.stderr)
        exit(1)

    path_to_descr_regions = path_to_base / "descr_regions.txt"
    if not path_to_descr_regions.is_file():
        print("Missing descr_regions.txt.", file=sys.stderr)
        exit(1)

    settlements = locate_settlements(path_to_map_regions, path_to_descr_regions)
    with open("settlements.csv", "w", encoding="utf-8") as f:
        f.write("settlement,x,y,r,g,b\n")
        for settlement in settlements:
            name = settlement["settlement"]
            x, y = settlement["coordinate"]
            r, g, b = settlement["color"]
            f.write(f"{name},{x},{y},{r},{g},{b}\n")
    print(f"{len(settlements)} settlements saved to settlements.csv")
