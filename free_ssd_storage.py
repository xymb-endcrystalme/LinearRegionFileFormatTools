#!/usr/bin/env python3
import os
import sys
import argparse
import shutil
from time import sleep
from tqdm import tqdm

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(1)

def create_symlink(source, destination):
    # create a symlink from source to destination
    if not os.path.exists(destination):
        os.symlink(source, destination)

def main(args):
    server_dir = args.server_dir.rstrip(os.sep)
    storage_dir = args.storage_dir.rstrip(os.sep)
    if not os.path.isdir(server_dir):
        raise ValueError(f"Server directory {server_dir} does not exist or is not a directory.")
    if not os.path.isdir(storage_dir):
        raise ValueError(f"Storage directory {storage_dir} does not exist or is not a directory.")
    print(f"Preparing a file list from {server_dir}, this can take a minute.")
    server_files = [f for f in os.listdir(server_dir)]
    print(f"Done.")
    progress_bar = tqdm(total=len(server_files), desc="Processing files", disable=args.verbose)

    for i, file_name in enumerate(server_files):
        if file_name.endswith(".linear") and not os.path.islink(os.path.join(server_dir, file_name)):
            moved = False
            server_file_path = os.path.join(server_dir, file_name)
            storage_file_path = os.path.join(storage_dir, file_name)
            if os.path.exists(storage_file_path) and os.path.isfile(storage_file_path):
                server_file_stat = os.stat(server_file_path)
                storage_file_stat = os.stat(storage_file_path)
                if server_file_stat.st_mtime == storage_file_stat.st_mtime and server_file_stat.st_size == storage_file_stat.st_size:
                    tmp_file_path = server_file_path + ".tmp"
                    create_symlink(storage_file_path, tmp_file_path)
                    tmp_file_stat = os.stat(tmp_file_path)
                    if tmp_file_stat.st_mtime == storage_file_stat.st_mtime and tmp_file_stat.st_size == storage_file_stat.st_size:
                        shutil.move(tmp_file_path, server_file_path)
                        moved = True
                        if args.verbose: print(f"{i}/{len(server_files)} - moved {file_name} to {storage_dir}")
                        if args.slow: sleep(args.slow)

            if moved == False and args.verbose:
                print(f"{i}/{len(server_files)} - ignoring {file_name}")
        if args.slow: sleep(args.slow / 100) # Slow down somewhat even if just looping
        progress_bar.update(1)
    progress_bar.close()

if __name__ == "__main__":
    parser = CustomArgumentParser(description="Free space from server and create symlinks to storage.")
    parser.add_argument("server_dir", help="minecraft server's region file directory (SSD)")
    parser.add_argument("storage_dir", help="region file storage directory (HDD)")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-s", "--slow", type=float, metavar="SECONDS", help="wait SECONDS seconds after each successful move")
    args = parser.parse_args()
    try:
        main(args)
    except ValueError as e:
        parser.error(str(e))