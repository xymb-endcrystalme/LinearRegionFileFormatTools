#!/usr/bin/env python3

import sys
import os
import os.path
import argparse
import zlib
from glob import glob
from linear import open_region_linear, write_region_anvil, open_region_anvil, write_region_linear
from multiprocessing import Pool, cpu_count, Manager
from tqdm import tqdm

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, _):
        self.print_help()
        sys.exit(1)

def convert_file(args):
    source_file, conversion_mode, destination_dir, compression_level, converted_counter, skipped_counter, log = args

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
        skipped_counter.value += 1
        return

    try:
        if conversion_mode == "linear2mca":
            region = open_region_linear(source_file)
            write_region_anvil(destination_file, region, compression_level=zlib.Z_DEFAULT_COMPRESSION)
        else:
            region = open_region_anvil(source_file)
            write_region_linear(destination_file, region, compression_level=compression_level)

        destination_size = os.path.getsize(destination_file)

        if log:
            print(source_file, "converted, compression %3d%%" % (100 * destination_size / source_size))
        converted_counter.value += 1
    except Exception:
        import traceback
        traceback.print_exc()
        print("Error with region file", source_file)

if __name__ == "__main__":
    parser = CustomArgumentParser(description="Convert region files between Anvil and Linear format")
    parser.add_argument("conversion_mode", choices=["mca2linear", "linear2mca"], help="Conversion direction: mca2linear or linear2mca")
    parser.add_argument("-t", "--threads", type=int, default=cpu_count(), help="Number of threads (default: number of CPUs)")
    parser.add_argument("-c", "--compression-level", type=int, default=6, help="Zstd compression level (default: 6)")
    parser.add_argument("-l", "--log", action='store_true', help="Show a log of files instead of a progress bar")
    parser.add_argument("source_dir", help="Source directory containing region files")
    parser.add_argument("destination_dir", help="Destination directory to store converted region files")

    args = parser.parse_args()

    threads = args.threads
    compression_level = args.compression_level
    source_dir = args.source_dir
    destination_dir = args.destination_dir
    log = args.log

    file_ext = "*.linear" if args.conversion_mode == "linear2mca" else "*.mca"
    file_list = glob(os.path.join(source_dir, file_ext))
    print("Found", len(file_list), "region files to convert")

    with Manager() as manager:
        converted_counter = manager.Value("i", 0)
        skipped_counter = manager.Value("i", 0)
        pool = Pool(threads)
        progress_bar = None
        if not log:
            progress_bar = tqdm(total=len(file_list), desc="Converting files")
        for _ in pool.imap_unordered(convert_file, [(file, args.conversion_mode, destination_dir, compression_level, converted_counter, skipped_counter, log) for file in file_list]):
            if progress_bar:
                progress_bar.update(1)
        if progress_bar: progress_bar.close()
        print(f"Conversion complete: {converted_counter.value} region files converted, {skipped_counter.value} region files skipped")
