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

        total_palette = {}
        '''
        for section in nbt["sections"]:
#            if section["Y"] == 1:

            if "block_states" in section and "data" in section["block_states"] and len(section["block_states"]["palette"]) >= 1:
                for element in section["block_states"]["palette"]:
                    s = str(element)
                    if s not in total_palette:
                        total_palette[s] = element

        print("Total palette length:", len(total_palette))
        '''
        TO_MERGE = 2

        offset = 0

        for i, section in enumerate(nbt["sections"]):
            if int(section["Y"] <= -5):
                offset += 1
                continue
            if "block_states" not in section or "data" not in section["block_states"] or len(section["block_states"]["palette"]) <= 1:
                print(section["Y"])
                break

            if (i - offset) % TO_MERGE == 0: previous_sections = []
            previous_sections.append(section)

            if (i - offset) % TO_MERGE != TO_MERGE - 1: continue

            print("Merging", len(previous_sections))

#            final_palette = nbtlib.tag.Compound()
            final_palette = []

            total_palette = {}
            palette_mappings = {}

            for section in previous_sections:
                for element in section["block_states"]["palette"]:
                    s = str(element)
                    if s not in total_palette:
                        total_palette[s] = element
                        palette_mappings[s] = len(palette_mappings)
                print("Palette:", len(section["block_states"]["palette"]))

            print("Total palette length:", len(total_palette))

            bits_per_block_final = max(4, math.ceil(math.log2(len(total_palette))))
            final_storage = SimpleBitStorage(bits_per_block_final, 4096 * TO_MERGE)

            for j, section in enumerate(previous_sections):
                mappings = []
                for element in section["block_states"]["palette"]:
                    s = str(element)
                    mappings.append(palette_mappings[s])
                print(mappings)

                palette_size = len(section["block_states"]["palette"])
                bits_per_block = max(4, math.ceil(math.log2(palette_size)))
                int_list = section["block_states"]["data"].tolist()
                storage = SimpleBitStorage(bits_per_block, 4096, int_list)

                decoded_values = []
                storage.get_all(lambda value: decoded_values.append(value))

                for v in range(4096):
                    final_storage.set(v + 4096 * j, mappings[decoded_values[v]])

            print(final_storage.get_raw())

            final_palette_mappings = [total_palette[k] for k, _ in sorted(palette_mappings.items(), key=lambda x: x[1])]
            print("Final palette mappings:", final_palette_mappings)

#            section["block_states"]["data"] = nbtlib.tag.LongArray(final_storage.get_raw())

        chunk.from_nbtlib(nbt)

    print()
    print("Original file size             :", os.path.getsize(INPUT_FILE))
    print("File size             :", os.path.getsize("/tmp/recompressed.linear"))

    mclinear.write_region_linear_v2("/tmp/recompressed2.linear", region)

    print("File size recompressed:", os.path.getsize("/tmp/recompressed2.linear"))

if __name__ == "__main__":
    main()
