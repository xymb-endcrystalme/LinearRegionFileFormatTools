#!/usr/bin/env python3

import sys
import os
import time
import math
import nbtlib

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import mclinear
from tools.simplebitstorage import SimpleBitStorage
from tools.secondbitstorage import SecondBitStorage

# Global variable to store the precomputed Hilbert curve
hilbert_lookup = []

def hilbert3d_precompute():
    """
    Precompute the 3D Hilbert curve for a 16x16x16 cube.
    """
    global hilbert_lookup
    hilbert_lookup = [0] * (16 * 16 * 16)

    def rot(n, x, y, z, rx, ry, rz):
        if ry == 0:
            if rz == 1:
                x = n-1 - x
                z = n-1 - z
            x, z = z, x
        return x, y, z

    def hilbert3d(x, y, z):
        d = 0
        s = 8
        while s > 0:
            rx = (x & s) > 0
            ry = (y & s) > 0
            rz = (z & s) > 0
            d += s * s * s * ((3 * rx) ^ ry ^ rz)
            x, y, z = rot(s, x, y, z, rx, ry, rz)
            s //= 2
        return d

    for x in range(16):
        for y in range(16):
            for z in range(16):
                index = x + (y << 4) + (z << 8)
                hilbert_lookup[index] = hilbert3d(x, y, z)

def hilbert3d_index(x, y, z):
    """
    Get the precomputed Hilbert curve index for given (x,y,z) coordinates.
    """
    return hilbert_lookup[x + (y << 4) + (z << 8)]

def get_file_size(file_path):
    return os.path.getsize(file_path)

def main():
    # Precompute the Hilbert curve
    hilbert3d_precompute()

    if False:
        INPUT_FILE = "/tmp/r.0.0.mca"
        region = mclinear.open_region_anvil(INPUT_FILE)
    else:
        INPUT_FILE = "/tmp/r.4.4.linear"
        INPUT_FILE = "/tmp/r.4.4.linear.copy"
        region = mclinear.open_region_linear_v2(INPUT_FILE)

    mclinear.write_region_linear_v2("/tmp/recompressed.linear", region)


    for chunk in region.chunks:
        if chunk == None: continue

        nbt = chunk.as_nbtlib()

        for section in nbt["sections"]:
#            if section["Y"] == 1:
            if "block_states" in section and "data" in section["block_states"] and len(section["block_states"]["palette"]) > 1:
                palette_size = len(section["block_states"]["palette"])
#                print("Palette size", palette_size)
#                print("aaa", section["block_states"]["data"])
#                print("toList", section["block_states"]["data"].tolist())

                int_list = section["block_states"]["data"].tolist()


                # Calculate bits per block
                bits_per_block = max(4, math.ceil(math.log2(palette_size)))

                # Create SimpleBitStorage
                storage = SimpleBitStorage(bits_per_block, 4096, int_list)
                
                # Decode and print all values
                decoded_values = []
                storage.get_all(lambda value: decoded_values.append(value))

#                for i, value in enumerate(decoded_values):

#                print(bits_per_block)
#                if bits_per_block == 4: bits_per_block = 9
#                if bits_per_block == 5: bits_per_block = 8
#                if bits_per_block == 6: bits_per_block = 8
#                if bits_per_block == 5: bits_per_block = 6
                second_storage = SecondBitStorage(bits_per_block, 4096)

                buckets = [0 for i in range(palette_size)]

                complete_list = []

                for i, value in enumerate(decoded_values):
                    x = i % 16
                    z = (i // 16) % 16
                    y = i // 256

                    hilbert_index = hilbert3d_index(x, y, z)
                    complete_list.append(hilbert_index)
                    second_storage.set(hilbert_index, value)
                    buckets[value] += 1

                print(sorted(complete_list))
                exit(0)

                section["block_states"]["data"] = nbtlib.tag.LongArray(second_storage.get_raw())
                largest = 0
                rest = 0
#                if section["Y"] == 1:
                if False:
                    print("Buckets:", len(buckets), int(section["Y"]))
                    sorted_buckets = sorted(enumerate(buckets), key=lambda x: x[1], reverse=True)
                    largest += sorted_buckets[0][1]
                    for i in range(1, len(sorted_buckets)):
                        rest += sorted_buckets[i][1]
                    for i, bucket in sorted_buckets:
                        print(i, bucket, section["block_states"]["palette"][i]["Name"])

                    print()
                    print(largest, "/", rest)

#                print()
#                print("a", int_list)
#                print("b", second_storage.get_raw())
                
#                print(type(section["block_states"]["data"]))
#                section["block_states"]["data"] = second_storage.get_raw()

                '''
                print("Decoded values:")
                for i, value in enumerate(decoded_values):
                    if value != 0:
                        y = i // 256
                        remainder = i % 256
                        x = remainder // 16
                        z = remainder % 16
                        print(f"Block {i} - {x} {y} {z}: {value}")
                '''
                '''
                # Convert to SecondBitStorage
                second_storage = SecondBitStorage(bits_per_block, 4096)
                for i, value in enumerate(decoded_values):
                    second_storage.set(i, value)
                print("\nSecondBitStorage get_raw():")
                print(second_storage.get_raw())
                '''

        chunk.from_nbtlib(nbt)

    print()
    print("Original file size             :", os.path.getsize(INPUT_FILE))
    print("File size             :", os.path.getsize("/tmp/recompressed.linear"))

    mclinear.write_region_linear_v2("/tmp/recompressed2.linear", region)

    print("File size recompressed:", os.path.getsize("/tmp/recompressed2.linear"))

if __name__ == "__main__":
    main()
