#!/usr/bin/env python3
import argparse
import os
import sys

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, _):
        self.print_help()
        sys.exit(1)

def main():
    parser = CustomArgumentParser(description='Compare server_dir and storage_dir')
    parser.add_argument('server_dir', help='Path to server directory')
    parser.add_argument('storage_dir', help='Path to storage directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print missing files')
    args = parser.parse_args()

    server_files = get_files(args.server_dir)
    storage_files = get_files(args.storage_dir)

    missing_files = find_missing_files(server_files, storage_files)

    if args.verbose:
        print_missing_files(missing_files)

    print_statistics(len(server_files), len(storage_files), len(missing_files))

    if len(missing_files) > 0:
        print("\033[31mMissing region files found\033[0m")
        sys.exit(1)
    else:
        print("\033[32mServer healthy\033[0m")

def get_files(dir_path):
    files = [f for f in os.listdir(dir_path) if f.endswith('.linear')]
    return set(files)

def find_missing_files(server_files, storage_files):
    return storage_files.difference(server_files)

def print_missing_files(missing_files):
    print("Missing files:")
    for f in missing_files:
        print(f)

def print_statistics(server_files_count, storage_files_count, missing_files_count):
    print("Statistics:")
    print("Server files: ", server_files_count)
    print("Storage files: ", storage_files_count)
    print("Missing files: ", missing_files_count)

if __name__ == "__main__":
    main()
