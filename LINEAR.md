# Linear File Format v1 Documentation

## Overview

The Linear v1 file format is an optimized storage format for Minecraft region files. It is designed to improve read and write performance, reduce storage space, and provide better compression compared to the traditional Anvil format.

## File Structure

A Linear v1 file consists of the following components:

1. Superblock (32 bytes)
2. Compressed Data
3. Footer (8 bytes)

### Superblock (32 bytes)

The superblock contains metadata about the file and has the following structure:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 8      | uint64 | Signature (0xc3ff13183cca9d9a) |
| 8      | 1      | uint8  | Version (1)                    |
| 9      | 8      | uint64 | Newest timestamp               |
| 17     | 1      | int8   | Compression level              |
| 18     | 2      | int16  | Chunk count                    |
| 20     | 4      | uint32 | Compressed data length         |
| 24     | 8      | uint64 | Reserved (currently unused)    |

### Compressed Data

The compressed data section contains the actual chunk data and metadata. It is compressed using the Zstandard (zstd) algorithm. When decompressed, it has the following structure:

1. Header (8192 bytes)
2. Chunk Data

#### Header (8192 bytes)

The header contains information about each chunk in the region (32x32 chunks). For each chunk, there are 8 bytes of metadata:

| Offset | Size   | Type   | Description     |
|--------|--------|--------|-----------------|
| 0      | 4      | uint32 | Chunk size      |
| 4      | 4      | uint32 | Chunk timestamp |

#### Chunk Data

The chunk data follows the header and contains the raw NBT data for each non-empty chunk in the region.

### Footer (8 bytes)

The footer contains a signature to verify the integrity of the file:

| Offset | Size   | Type   | Description                    |
|--------|--------|--------|--------------------------------|
| 0      | 8      | uint64 | Signature (0xc3ff13183cca9d9a) |

## File Naming Convention

Linear v1 files follow the naming convention:

r.<region_x>.<region_z>.linear

Where `<region_x>` and `<region_z>` are the region coordinates.

## Chunk Storage

In Linear v1, chunks are stored sequentially after the header. The chunk size in the header determines the length of each chunk's data. If a chunk's size is 0, it means the chunk is empty or doesn't exist.

## Compression

The entire data section (header + chunk data) is compressed using Zstandard (zstd) algorithm. The compression level is specified in the superblock.

## Advantages over Anvil Format

1. Single compression operation for the entire region, potentially resulting in better compression ratios.
2. Simplified structure with no need for sector-based storage.
3. Quick access to chunk metadata (size and timestamp) without decompressing the entire file.
4. Improved write performance due to the append-only nature of the format.

## Limitations

1. Updating a single chunk requires rewriting the entire file.
2. No support for partial region loading (all chunks must be decompressed to access any single chunk).

## Compatibility

Linear v1 format is not directly compatible with the Anvil format and requires conversion tools to switch between the two formats.
