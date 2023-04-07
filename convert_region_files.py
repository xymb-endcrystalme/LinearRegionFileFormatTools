#!/usr/bin/env python3

import sys
import os
import os.path
import argparse
from glob import glob
from linear import open_region_linear, write_region_anvil, open_region_anvil, write_region_linear
from multiprocessing import Pool, cpu_count

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(1)

def convert_file(args):
    source_file, conversion_mode, destination_dir, compression_level = args

    os.makedirs(destination_dir, exist_ok=True)

    source_filename = os.path.basename(source_file)
    destination_file = os.path.join(destination_dir, source_filename).rpartition(".")[0] + (".mca" if conversion_mode == "linear2mca" else ".linear")

    convert = False
    try:
        mtime_destination = os.path.getmtime(destination_file)
        mtime_source = os.path.getmtime(source_file)
        if mtime_destination != mtime_source:
            convert = True
    except FileNotFoundError:
        convert = True

    source_size = os.path.getsize(source_file)
    if not convert or source_size == 0:
        return

    try:
        if conversion_mode == "linear2mca":
            region = open_region_linear(source_file)
            write_region_anvil(destination_file, region, compression_level=compression_level)
        else:
            region = open_region_anvil(source_file)
            write_region_linear(destination_file, region, compression_level=compression_level)

        destination_size = os.path.getsize(destination_file)

        print(source_file, "converted, compression %3d%%" % (100 * destination_size / source_size))
    except Exception:
        import traceback
        traceback.print_exc()
        print("Error with region file", source_file)

if __name__ == "__main__":
    parser = CustomArgumentParser(description="Convert region files between Anvil and Linear format")
    parser.add_argument("conversion_mode", choices=["mca2linear", "linear2mca"], help="Conversion direction: mca2linear or linear2mca")
    parser.add_argument("-t", "--threads", type=int, default=cpu_count(), help="Number of threads (default: number of CPUs)")
    parser.add_argument("-c", "--compression-level", type=int, default=6, help="Compression level (default: 6)")
    parser.add_argument("source_dir", help="Source directory containing region files")
    parser.add_argument("destination_dir", help="Destination directory to store converted region files")

    args = parser.parse_args()

    threads = args.threads
    compression_level = args.compression_level
    source_dir = args.source_dir
    destination_dir = args.destination_dir

    file_ext = "*.linear" if args.conversion_mode == "linear2mca" else "*.mca"
    file_list = glob(os.path.join(source_dir, file_ext))
    print("Found", len(file_list), "files to convert")

    pool = Pool(threads)
    pool.map(convert_file, [(file, args.conversion_mode, destination_dir, compression_level) for file in file_list])
