#!/usr/bin/env python3

import sys
import os
import time

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import mclinear

def get_file_size(file_path):
    return os.path.getsize(file_path)

def main():
#    input_file = "/home/bc/.local/share/PrismLauncher/instances/Vanilla/.minecraft/saves/aaaaa/region/r.0.0.mca"
    input_file = "/tmp/r.0.0.mca"

    region = mclinear.open_region_anvil(input_file)
    nbt = region.chunks[0].as_nbtlib()

    for section in nbt["sections"]:
        if section["Y"] == 0:
            palette_size = len(section["block_states"]["palette"])
            print("Palette size", palette_size)
            print("aaa", section["block_states"]["data"])
            print("toList", section["block_states"]["data"].tolist())

            int_list = section["block_states"]["data"].tolist()


if __name__ == "__main__":
    main()
