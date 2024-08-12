# Linear File Format v2 Documentation

## Overview

The Linear v2 file format is an enhanced version of the original Linear file format, designed to further optimize storage and performance for Minecraft region files. It introduces a grid-based compression scheme for better data management and flexibility.

## File Structure

A Linear v2 file consists of the following components:

1. Superblock (26 bytes)
2. Chunk Existence Bitmap (128 bytes)
3. NBT Features
4. Bucket Sizes
5. Compressed Data
6. Footer (8 bytes)

### Superblock (26 bytes)

The superblock contains metadata about the file and has the following structure:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 8      | uint64 | Signature (0xc3ff13183cca9d9a) |
| 8      | 1      | uint8  | Version (2)                    |
| 9      | 8      | uint64 | Newest timestamp               |
| 17     | 1      | int8   | Grid size                      |
| 18     | 4      | int32  | Region X                       |
| 22     | 4      | int32  | Region Z                       |

### Chunk Existence Bitmap (128 bytes)

A 1024-bit bitmap that indicates if a chunk exists or not. It is serialized into 128 bytes, where each bit represents the existence of a chunk. This allows for quick checking of chunk existence without decompressing the entire file.

### NBT Features

The NBT features section contains additional features and optimizations applied to the NBT data. It is a serialized dictionary with the following structure:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 1      | uint8  | Key length                     |
| 1      | -      | string | Key                            |
| -      | 4      | uint32 | Value                          |
| ...    | ...    | ...    | (Repeats for each key-value pair) |
| -      | 1      | uint8  | End marker (0)                 |

### Bucket Sizes

The bucket sizes section contains the sizes, compression levels, and xxhash64 of each bucket in the grid. Each bucket size entry has the following structure:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 4      | uint32 | Bucket size                    |
| 4      | 1      | int8   | Compression level              |
| 5      | 8      | uint64 | Bucket xxhash64                |

This section repeats for each bucket in the grid (grid_size * grid_size times).

### Compressed Data

The compressed data section contains the actual chunk data and metadata. It is divided into buckets based on the grid size. Each bucket is compressed using the Zstandard (zstd) algorithm.

### Footer (8 bytes)

The footer contains a signature to verify the integrity of the file:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 8      | uint64 | Signature (0xc3ff13183cca9d9a) |

## File Naming Convention

Linear v2 files follow the naming convention:

r.<region_x>.<region_z>.linear

Where `<region_x>` and `<region_z>` are the region coordinates.

## Grid System

The grid system divides the region into smaller sub-regions for more efficient compression. The grid size can be 1, 2, 4, 8, 16, or 32. Each grid cell contains a subset of the region's chunks.

## Chunk Data Structure

Within each bucket, chunks are stored with the following structure:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 4      | uint32 | Chunk size (including metadata)|
| 4      | 8      | uint64 | Chunk timestamp                |
| 12     | -      | bytes  | Chunk data (NBT)               |

If a chunk does not exist, only the size (0) and timestamp are stored.

## Advantages over Linear v1

1. Grid-based compression allows for more efficient partial region updates.
2. Chunk existence bitmap enables quick checking of chunk existence without decompression.
3. Flexible grid size allows for optimization based on world characteristics and usage patterns.
4. Improved integrity checking with xxhash64 for each bucket.

## Compatibility

Linear v2 format is not directly compatible with the Linear v1 or Anvil formats and requires conversion tools to switch between the formats.
