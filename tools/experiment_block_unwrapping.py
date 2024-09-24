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

def get_file_size(file_path):
    return os.path.getsize(file_path)

def main():
#    input_file = "/home/bc/.local/share/PrismLauncher/instances/Vanilla/.minecraft/saves/aaaaa/region/r.0.0.mca"
    input_file = "/tmp/r.0.0.mca"

    region = mclinear.open_region_anvil(input_file)
    nbt = region.chunks[0].as_nbtlib()

    for section in nbt["sections"]:
        if section["Y"] == 1:
            palette_size = len(section["block_states"]["palette"])
            print("Palette size", palette_size)
            print("aaa", section["block_states"]["data"])
            print("toList", section["block_states"]["data"].tolist())

            int_list = section["block_states"]["data"].tolist()
            
            # Calculate bits per block
            bits_per_block = max(4, math.ceil(math.log2(palette_size)))
            
            # Create SimpleBitStorage
            storage = SimpleBitStorage(bits_per_block, 4096, int_list)
            
            # Decode and print all values
            decoded_values = []
            storage.get_all(lambda value: decoded_values.append(value))
            
            print("Decoded values:")
            for i, value in enumerate(decoded_values):
                if value != 0:
                    y = i // 256
                    remainder = i % 256
                    x = remainder // 16
                    z = remainder % 16
                    print(f"Block {i} - {x} {y} {z}: {value}")
            # Convert to SecondBitStorage
            second_storage = SecondBitStorage(bits_per_block, 4096)
            for i, value in enumerate(decoded_values):
                second_storage.set(i, value)
            print("\nSecondBitStorage get_raw():")
            print(second_storage.get_raw())

            # Update the NBT data with the new SecondBitStorage data
            section["block_states"]["data"] = nbtlib.tag.LongArray(second_storage.get_raw())

if __name__ == "__main__":
    main()
