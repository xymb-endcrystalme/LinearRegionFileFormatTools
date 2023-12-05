#!/usr/bin/env python3

import nbtlib
import sys
import argparse
import shutil

# TODO: Ender chest

def fix_player(file_path):
    nbt_file = nbtlib.load(file_path)

    fixed = False
    removed_items = 0

    for i, nbt in enumerate(nbt_file["Inventory"]):
        if "tag" in nbt:
            nbt = nbt["tag"]
            if "BlockEntityTag" in nbt:
                nbt = nbt["BlockEntityTag"]
                if "Items" in nbt:
                    length = len(nbt["Items"])
                    if length > 27:
                        nbt["Items"] = nbtlib.tag.List[nbtlib.tag.Compound]()
                        fixed = True
                        removed_items += 1

    if fixed == True:
        print("Fixed! Removed {} items.".format(removed_items))
        backup_path = file_path + ".ban.bak"
        shutil.copyfile(file_path, backup_path)
        nbt_file.save(file_path)

def main():
    parser = argparse.ArgumentParser(description="Print the contents of a user's playerdata NBT file.")
    parser.add_argument('file', type=str, help='Path to the NBT file to be read.')
    args = parser.parse_args()

    fix_player(args.file)

if __name__ == "__main__":
    main()