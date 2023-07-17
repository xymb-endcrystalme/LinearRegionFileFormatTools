#!/usr/bin/env python3

import sys
import zlib
import nbtlib
import random
from linear import open_region_linear, write_region_linear

source_filename = sys.argv[1]
destination_filename = sys.argv[2]

dest_region_coords = destination_filename.split("/")[-1].split(".")
dest_region_x = int(dest_region_coords[1])
dest_region_z = int(dest_region_coords[2])

src_region_coords = source_filename.split("/")[-1].split(".")
src_region_x = int(src_region_coords[1])
src_region_z = int(src_region_coords[2])

region_diff_x, region_diff_z = dest_region_x - src_region_x, dest_region_z - src_region_z
block_diff_x, block_diff_z = (dest_region_x - src_region_x) * 512, (dest_region_z - src_region_z) * 512
chunk_diff_x, chunk_diff_z = (dest_region_x - src_region_x) * 32, (dest_region_z - src_region_z) * 32

print("Source coords:", src_region_x * 512, src_region_z * 512)
print("Destination coords:", dest_region_x * 512, dest_region_z * 512)
print("Coord difference:", block_diff_x, block_diff_z)
print("Chunk difference:", chunk_diff_x, chunk_diff_z)

region = open_region_linear(source_filename)
for chunk in region.chunks:
    if chunk == None: continue

    nbt = chunk.as_nbtlib()
    is_region = 'xPos' in nbt
    is_entities = 'Entities' in nbt
    if is_region:
        chunk_x, chunk_z = int(nbt['xPos']), int(nbt['zPos'])
        print("Region chunk:", chunk_x, chunk_z)
        if chunk_x != chunk.x or chunk_z != chunk.z:
            raise Exception("Coord mismatch")

        nbt['xPos'] = nbtlib.Int(int(nbt['xPos']) + chunk_diff_x)
        nbt['zPos'] = nbtlib.Int(int(nbt['zPos']) + chunk_diff_z)
        chunk.x, chunk.z = int(nbt['xPos']), int(nbt['zPos'])

        for start in nbt['structures']['starts']:
            structure = nbt['structures']['starts'][start]

            structure["ChunkX"] = nbtlib.Int(int(structure["ChunkX"]) + chunk_diff_x)
            structure["ChunkZ"] = nbtlib.Int(int(structure["ChunkZ"]) + chunk_diff_z)

        for block_entity in nbt["block_entities"]:
            x, z = int(block_entity["x"]), int(block_entity["z"])
            x += block_diff_x
            z += block_diff_z
            block_entity["x"] = nbtlib.Int(x)
            block_entity["z"] = nbtlib.Int(z)

            # Verify
            if not chunk.x * 16 <= x < (chunk.x + 1) * 16: raise Exception("Block entity coord mismatch X " + str(chunk.x * 16) + " " + str(x))
            if not chunk.z * 16 <= z < (chunk.z + 1) * 16: raise Exception("Block entity coord mismatch Z " + str(chunk.z * 16) + " " + str(z))

    elif is_entities:
        chunk_x, chunk_z = int(nbt['Position'][0]), int(nbt['Position'][1])
        print("Entities chunk:", chunk_x, chunk_z)
        if chunk_x != chunk.x or chunk_z != chunk.z:
            raise Exception("Coord mismatch")

        nbt['Position'] = nbtlib.IntArray([nbtlib.Int(int(nbt['Position'][0]) + chunk_diff_x), nbtlib.Int(int(nbt['Position'][1]) + chunk_diff_z)])
        chunk.x, chunk.z = int(nbt['Position'][0]), int(nbt['Position'][1])

        def move_entity(entity):
            if 'TileX' in entity: entity['TileX'] = nbtlib.Int(int(entity['TileX'] + block_diff_x))
            if 'TileZ' in entity: entity['TileZ'] = nbtlib.Int(int(entity['TileZ'] + block_diff_z))

            if 'HomePosX' in entity: entity['HomePosX'] = nbtlib.Int(int(entity['HomePosX'] + block_diff_x))
            if 'HomePosZ' in entity: entity['HomePosZ'] = nbtlib.Int(int(entity['HomePosZ'] + block_diff_z))

            if 'Paper.Origin' in entity:
                entity['Paper.Origin'][0] = nbtlib.Double(float(entity['Paper.Origin'][0]) + block_diff_x)
                entity['Paper.Origin'][2] = nbtlib.Double(float(entity['Paper.Origin'][2]) + block_diff_z)

            entity['Pos'][0] = nbtlib.Double(float(entity['Pos'][0]) + block_diff_x)
            entity['Pos'][2] = nbtlib.Double(float(entity['Pos'][2]) + block_diff_z)

            if 'UUID' in entity:
                entity['UUID'] = nbtlib.IntArray([random.randint(-2**31, 2**31), random.randint(-2**31, 2**31), random.randint(-2**31, 2**31), random.randint(-2**31, 2**31)])

            # Verify
            if not chunk.x * 16 <= float(entity['Pos'][0]) < (chunk.x + 1) * 16: raise Exception("Block entity coord mismatch X " + str(chunk.x * 16) + " " + str(entity['Pos'][0]))
            if not chunk.z * 16 <= float(entity['Pos'][2]) < (chunk.z + 1) * 16: raise Exception("Block entity coord mismatch Z " + str(chunk.z * 16) + " " + str(entity['Pos'][2]))

            if 'Passengers' in entity:
                for subentity in entity['Passengers']: move_entity(subentity)

        for entity in nbt['Entities']:
            move_entity(entity)

    chunk.from_nbtlib(nbt)

region.region_x += region_diff_x
region.region_z += region_diff_z

write_region_linear(destination_filename, region)
