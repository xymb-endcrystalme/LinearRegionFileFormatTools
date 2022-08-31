#!/usr/bin/python3

import sys
import os
import os.path
from glob import glob
from linear import Chunk, Region, write_region_linear, open_region_anvil

if len(sys.argv) != 3:
    print("Usage: source_dir destination_dir")
    exit(0)

source_dir = sys.argv[1]
destination_dir = sys.argv[2]

for source_file in glob(os.path.join(source_dir, "*.mca")):
    os.makedirs(destination_dir, exist_ok=True)
    
    source_filename = os.path.basename(source_file)
    destination_file = os.path.join(destination_dir, source_filename).rpartition(".")[0] + ".linear"

    convert_to_linear = False
    try:
        mtime_destination = os.path.getmtime(destination_file)
        mtime_source = os.path.getmtime(source_file)
        if mtime_destination != mtime_source:
            convert_to_linear = True
    except FileNotFoundError:
        convert_to_linear = True

    source_size = os.path.getsize(source_file)
    if convert_to_linear == False or source_size == 0:
        print(source_filename, "already converted, skipping")
        continue

    region = open_region_anvil(source_file)
    write_region_linear(destination_file, region, compression_level=1)

    source_size = os.path.getsize(source_file)
    destination_size = os.path.getsize(destination_file)

    print(source_file, "converted, compression %3d%%" % (100 * destination_size / source_size))
