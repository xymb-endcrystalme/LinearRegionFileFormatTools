#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, _):
        self.print_help()
        sys.exit(1)

def main(args):
    cutoff_date = datetime.strptime(args.cutoff_date, '%d-%m-%Y')
    source_directory = args.source_directory
    progress = args.progress

    new_files_count = 0
    new_files_size = 0
    old_files_count = 0
    old_files_size = 0
    count = 0

    for root, dirs, files in os.walk(source_directory, followlinks=False):
        for file in files:
            if file.endswith(".linear"):
                file_path = os.path.join(root, file)
                if not os.path.islink(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    file_date = datetime.fromtimestamp(file_mtime)
                    file_size = os.path.getsize(file_path)
                    
                    if file_date > cutoff_date:
                        new_files_count += 1
                        new_files_size += file_size
                    else:
                        old_files_count += 1
                        old_files_size += file_size

                count += 1
                if progress and count % 1000 == 0:
                    print(f"Processed {count} files")

    print(f"New file count: {new_files_count}")
    print(f"New files size: {new_files_size} bytes")
    print(f"Old file count: {old_files_count}")
    print(f"Old files size: {old_files_size} bytes")

if __name__ == "__main__":
    parser = CustomArgumentParser(description="Process files based on a cutoff date and source directory.")
    parser.add_argument("-p", "--progress", const=True, nargs="?", default=False, help="Print a progress log")
    parser.add_argument("cutoff_date", help="Cutoff date in DD-MM-YYYY format")
    parser.add_argument("source_directory", help="Source directory to process files from")
    args = parser.parse_args()
    main(args)
