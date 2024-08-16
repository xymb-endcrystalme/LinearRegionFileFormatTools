#!/usr/bin/env python3

import sys
import os
import csv

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from mclinear import open_region_linear

def main():
    if len(sys.argv) != 3:
        print("Usage: python scan_for_bases.py <path> <csv_file>")
        sys.exit(1)

    path = sys.argv[1]
    csv_file = sys.argv[2]

    if not os.path.isdir(path):
        print(f"Error: {path} is not a valid directory")
        sys.exit(1)

    # Get all .linear files in the directory
    linear_files = [f for f in os.listdir(path) if f.endswith('.linear')]

    # Sort files by modification time (newest first)
    linear_files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)

    total_files = len(linear_files)
    files_with_high_hash_count = 0

    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Region X', 'Region Z', 'Hash Count'])  # Write header

        for index, file in enumerate(linear_files, 1):
            file_path = os.path.join(path, file)
            
            # Check if the file is a symlink right before opening it
            if os.path.islink(file_path):
                print(f"Skipping symlink: {file_path}")
                continue

            try:
                print(f"Processing {file_path}")
                region = open_region_linear(file_path)

                hash_count = 0
                for chunk in region.chunks:
                    if chunk is not None:
                        hash_count += chunk.raw_chunk.count(b"hash")
                print(f"Region {region.region_x}, {region.region_z} - Hashes: {hash_count}")

                # Write to CSV file
                csv_writer.writerow([region.region_x, region.region_z, hash_count])
                csvfile.flush()  # Ensure data is written immediately

                if hash_count > 100:
                    files_with_high_hash_count += 1

                # Print progress
                print(f"Progress: {index}/{total_files} files processed")
                print(f"Files with hash count > 100: {files_with_high_hash_count}")
                print("--------------------")

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

    print(f"\nScan completed. Total files processed: {total_files}")
    print(f"Total files with hash count > 100: {files_with_high_hash_count}")

if __name__ == "__main__":
    main()
