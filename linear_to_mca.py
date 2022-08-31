#!/usr/bin/python3

import sys

from linear import Chunk, Region, open_region_linear, write_region_anvil

filename = sys.argv[1]
filename_anvil = filename.rpartition('.')[0] + ".mca"
print("Converting " + filename + " to " + filename_anvil)

region = open_region_linear(filename)
write_region_anvil(filename_anvil, region, compression_level=zlib.Z_DEFAULT_COMPRESSION)
