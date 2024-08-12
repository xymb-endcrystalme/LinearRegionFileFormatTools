#!/usr/bin/env python3
import os
import argparse
import linear

class FinishedException(Exception):
    pass

def verify_region_file_is_fully_filled(file_path):
    if not os.path.isfile(file_path): return False
    region = linear.open_region_linear(file_path)
    for chunk in region.chunks:
        if chunk == None: return False
    return True

def verify(path_to_files, dx, dz):
    file_name = f"r.{dx}.{dz}.linear"
    full_path = os.path.join(path_to_files, file_name)
    if not verify_region_file_is_fully_filled(full_path):
        print(f"File {full_path} failed verification")
        raise FinishedException
        return False
    else:
        print(f"File {full_path} ok")
        return True


def main(path_to_files):
    biggest_rectangle_size = 0
    try:
        for rectangle_size in range(0, 1000):
            for dx in range(-rectangle_size - 1, rectangle_size + 1):
                dz = rectangle_size
                verify(path_to_files, dx, dz)
                dz = -rectangle_size - 1
                verify(path_to_files, dx, dz)
            for dz in range(-rectangle_size - 0, rectangle_size + 0):
                dx = rectangle_size
                verify(path_to_files, dx, dz)
                dx = -rectangle_size - 1
                verify(path_to_files, dx, dz)
            biggest_rectangle_size = rectangle_size
    except FinishedException as ex: pass

    print("Safe spawn size:", biggest_rectangle_size, "region files")
    print("Safe spawn size:", biggest_rectangle_size * 16, "chunks")
    print("Safe spawn size:", biggest_rectangle_size * 512, "blocks")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process region files.')
    parser.add_argument('path', metavar='path_to_files', type=str, help='Path to the region files')
    
    args = parser.parse_args()
    
    main(args.path)
