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
    input_file = "/tmp/r.0.10030.linear"
    output_file = "/tmp/result.linear"

    # Get initial file size
    initial_size = get_file_size(input_file)

    # Measure time for opening and writing
    start_time = time.time()
    
    # Open the region file
    region = mclinear.open_region_linear(input_file)
    
    # Write the compressed region file
    mclinear.write_region_linear_v2(output_file, region)
    
    end_time = time.time()

    # Get final file size
    final_size = get_file_size(output_file)

    # Calculate compression time and ratio
    compression_time = end_time - start_time
    compression_ratio = initial_size / final_size

    # Print summary
    print(f"Compression Summary:")
    print(f"Initial file size: {initial_size:,} bytes")
    print(f"Final file size: {final_size:,} bytes")
    print(f"Compression time: {compression_time:.2f} seconds")
    print(f"Compression ratio: {compression_ratio:.2f}:1")

if __name__ == "__main__":
    main()
