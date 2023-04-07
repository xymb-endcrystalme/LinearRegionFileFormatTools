#!/usr/bin/env python3

import sys

from linear import Chunk, Region, write_region_linear, open_region_anvil

filename_anvil = sys.argv[1]
filename = filename_anvil.rpartition('.')[0] + ".linear"
print("Converting " + filename_anvil + " to " + filename)

region = open_region_anvil(filename_anvil)
write_region_linear(filename, region)
