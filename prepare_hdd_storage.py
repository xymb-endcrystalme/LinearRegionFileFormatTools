#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
from datetime import datetime
from tqdm import tqdm

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, _):
        self.print_help()
        sys.exit(1)

def main(source_dir, dest_dir, cutoff_date):
    print(f"Preparing a file list from {source_dir}, this can take a minute.")
    files = os.listdir(source_dir)
    files_to_copy = [f for f in files if f.endswith(".linear")]

    copied_files = 0
    skipped_files = 0
    already_exists_files = 0
    symlink_files = 0

    try:
        for file in tqdm(files_to_copy, desc="Copying files"):
            src_path = os.path.join(source_dir, file)
            dest_path = os.path.join(dest_dir, file)
            dest_tmp_path = dest_path + ".tmp"

            if os.path.islink(src_path):
                symlink_files += 1
                continue

            if not os.path.isfile(src_path):
                skipped_files += 1
                continue

            file_mtime = os.path.getmtime(src_path)
            file_datetime = datetime.fromtimestamp(file_mtime)

            if file_datetime < cutoff_date:
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_tmp_path)
                    os.rename(dest_tmp_path, dest_path)
                    copied_files += 1
                else:
                    dest_mtime = os.path.getmtime(dest_path)
                    dest_size = os.path.getsize(dest_path)

                    if file_mtime > dest_mtime or os.path.getsize(src_path) != dest_size:
                        shutil.copy2(src_path, dest_tmp_path)
                        os.rename(dest_tmp_path, dest_path)
                        copied_files += 1
                    else:
                        already_exists_files += 1
            else:
                skipped_files += 1
    except KeyboardInterrupt:
        pass

    print(f"Copied region files: {copied_files}")
    print(f"Skipped region files: {skipped_files}")
    print(f"Already existing region files: {already_exists_files}")
    print(f"Symlink files ignored: {symlink_files}")

if __name__ == "__main__":
    parser = CustomArgumentParser(description="Copy files with certain conditions")
    parser.add_argument("cutoff", type=str, help="Cutoff date in the format YYYY-MM-DD")
    parser.add_argument("source", type=str, help="Source directory")
    parser.add_argument("destination", type=str, help="Destination directory")

    args = parser.parse_args()

    source_dir = args.source
    dest_dir = args.destination
    cutoff_date = datetime.strptime(args.cutoff, "%Y-%m-%d")

    main(source_dir, dest_dir, cutoff_date)
