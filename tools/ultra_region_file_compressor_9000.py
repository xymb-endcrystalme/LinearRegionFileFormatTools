#!/usr/bin/env python3

import sys
import os
import csv

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import mclinear

region = mclinear.open_region_linear("/tmp/r.0.10030.linear")
mclinear.write_region_linear_v2("/tmp/result.linear")