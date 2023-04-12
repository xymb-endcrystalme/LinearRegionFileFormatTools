import os
import struct
import pyzstd
import zlib

class Chunk:
    def __init__(self, raw_chunk, x, z):
        self.raw_chunk = raw_chunk
        self.x, self.z = x, z

    def __str__(self):
        return "Chunk %d %d - %d bytes" % (self.x, self.z, len(self.raw_chunk))

class Region:
    def __init__(self, chunks, region_x, region_z, mtime, timestamps):
        self.chunks = chunks
        self.region_x, self.region_z = region_x, region_z
        self.mtime = mtime
        self.timestamps = timestamps

    def chunk_count(self):
        count = 0
        for i in self.chunks:
            count += 1
        return count

REGION_DIMENSION = 32
COMPRESSION_TYPE = b'\x02'
COMPRESSION_TYPE_ZLIB = 2
EXTERNAL_FILE_COMPRESSION_TYPE = 128 + 2
LINEAR_SIGNATURE = 0xc3ff13183cca9d9a
LINEAR_VERSION = 1

# TODO: Alert users if the file name isn't r.0.0.linear

def open_region_linear(file_path):
    HEADER_SIZE = REGION_DIMENSION * REGION_DIMENSION * 8

    file_coords = file_path.split('/')[-1].split('.')[1:3]
    region_x, region_z = int(file_coords[0]), int(file_coords[1])

    raw_region = open(file_path, 'rb').read()
    mtime = os.path.getmtime(file_path)

    signature, version, newest_timestamp, compression_level, chunk_count, complete_region_length, reserved = struct.unpack_from(">QBQbhIQ", raw_region, 0)

    if signature != LINEAR_SIGNATURE:
        raise Exception("Superblock invalid")
    if version != LINEAR_VERSION:
        raise Exception("Version invalid")

    signature = struct.unpack(">Q", raw_region[-8:])[0]

    if signature != LINEAR_SIGNATURE:
        raise Exception("Footer signature invalid")

    decompressed_region = pyzstd.decompress(raw_region[32:-8])

    sizes = []
    timestamps = []

    real_chunk_count = 0
    total_size = 0
    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        size, timestamp = struct.unpack_from(">II", decompressed_region, i * 8)
        total_size += size
        if size != 0: real_chunk_count += 1
        sizes.append(size)
        timestamps.append(timestamp)

    if total_size + HEADER_SIZE != len(decompressed_region):
        raise Exception("Decompressed size invalid")

    if real_chunk_count != chunk_count:
        raise Exception("Chunk count invalid")

    chunks = [None] * REGION_DIMENSION * REGION_DIMENSION

    iterator = HEADER_SIZE
    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        if sizes[i] > 0:
            chunks[i] = Chunk(decompressed_region[iterator: iterator + sizes[i]], REGION_DIMENSION * region_x + i % 32, REGION_DIMENSION * region_z + i // 32)
        iterator += sizes[i]

    return Region(chunks, region_x, region_z, mtime, timestamps)

def quickly_verify_linear(file_path):
    try:
        raw_region = open(file_path, 'rb').read()
    except FileNotFoundError: return False
    mtime = os.path.getmtime(file_path)

    signature, version, newest_timestamp, compression_level, chunk_count, complete_region_length, hash64 = struct.unpack_from(">QBQbhIQ", raw_region, 0)

    if signature != LINEAR_SIGNATURE:
        return False
    if version != LINEAR_VERSION:
        return False

    signature = struct.unpack(">Q", raw_region[-8:])[0]

    if signature != LINEAR_SIGNATURE:
        return False

    return True

def write_region_linear(destination_filename, region: Region, compression_level=1):
    inside_header = []
    newest_timestamp = 0
    chunk_count = 0

    for i in range(32**2):
        if region.chunks[i] != None:
            inside_header.append(struct.pack(">II", len(region.chunks[i].raw_chunk), region.timestamps[i]))
            newest_timestamp = max(region.timestamps[i], newest_timestamp)
            chunk_count += 1
        else:
            inside_header.append(b"\x00" * 8)

    chunks = []

    for i in range(32**2):
        if region.chunks[i] != None:
            chunks.append(region.chunks[i].raw_chunk)
        else:
            chunks.append(b"")

    complete_region = b''.join(inside_header) + b''.join(chunks)
    complete_region_hash = b"\x00" * 8

    option = {pyzstd.CParameter.compressionLevel : compression_level,
                pyzstd.CParameter.checksumFlag : 1}
    complete_region = pyzstd.compress(complete_region, level_or_option=option)

    preheader = struct.pack(">QBQbhI", LINEAR_SIGNATURE, LINEAR_VERSION, newest_timestamp, compression_level, chunk_count, len(complete_region))
    footer = struct.pack(">Q", LINEAR_SIGNATURE)

    print("WRITE HASH", complete_region_hash)
    final_region_file = preheader + complete_region_hash + complete_region + footer

    with open(destination_filename + ".wip", "wb") as f:
        f.write(final_region_file)
        f.flush()
        os.fsync(f.fileno()) # Ensure atomicity on Btrfs
    os.utime(destination_filename + ".wip", (region.mtime, region.mtime))
    os.rename(destination_filename + ".wip", destination_filename)

def open_region_anvil(file_path):
    SECTOR = 4096

    chunk_starts = []
    chunk_sizes = []
    timestamps = []
    chunks = []

    file_coords = file_path.split('/')[-1].split('.')[1:3]
    region_x, region_z = int(file_coords[0]), int(file_coords[1])

    mtime = os.path.getmtime(file_path)
    anvil_file = open(file_path, 'rb').read()

    source_folder = file_path.rpartition("/")[0]

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        a, b, c, sector_count = struct.unpack_from(">BBBB", anvil_file, i * 4)
        chunk_starts.append(c + b * 256 + a * 256 * 256)
        chunk_sizes.append(sector_count)

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        timestamps.append(struct.unpack_from(">I", anvil_file, SECTOR + i * 4)[0])

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        if chunk_starts[i] > 0 and chunk_sizes[i] > 0:
            whole_raw_chunk = anvil_file[SECTOR * chunk_starts[i]:SECTOR * (chunk_starts[i] + chunk_sizes[i])]
            chunk_size, compression_type = struct.unpack_from(">IB", whole_raw_chunk, 0)
            if compression_type == COMPRESSION_TYPE_ZLIB:
                chunks.append(Chunk(zlib.decompress(whole_raw_chunk[5:5 + chunk_size]), REGION_DIMENSION * region_x + i % 32, REGION_DIMENSION * region_z + i // 32))
            elif compression_type == EXTERNAL_FILE_COMPRESSION_TYPE:
                external_file = open(source_folder + "/c.%d.%d.mcc" % (REGION_DIMENSION * region_x + i % 32, REGION_DIMENSION * region_z + i // 32), "rb").read()
                chunks.append(Chunk(zlib.decompress(external_file), REGION_DIMENSION * region_x + i % 32, REGION_DIMENSION * region_z + i // 32))
            else:
                raise Exception("Compression type %d unimplemented!" % (compression_type))
        else:
            chunks.append(None)

    return Region(chunks, region_x, region_z, mtime, timestamps)


def write_region_anvil(destination_filename, region: Region, compression_level=zlib.Z_DEFAULT_COMPRESSION):
    SECTOR = 4096

    destination_folder = destination_filename.rpartition("/")[0]
    header_chunks = []
    header_timestamps = []
    sectors = []
    start_sectors = []
    free_sector = 2

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        start_sectors.append(free_sector)
        if region.chunks[i] != None:
            compressed = zlib.compress(region.chunks[i].raw_chunk, compression_level)
            final_chunk_data = struct.pack(">I", len(compressed) + 1) + COMPRESSION_TYPE + compressed

            padding = 4096 - (len(final_chunk_data) % 4096)
            if padding == 4096:
                padding = 0
            final_chunk_data += b'\x00' * padding

            sector_count = len(final_chunk_data) // 4096
            if sector_count > 255:
                x, z = i % 32, i // 32
                print("Chunk in external file", region.region_x * 32 + x, region.region_z * 32 + z)
                chunk_file_path = destination_folder + "/c.%d.%d.mcc" % (region.region_x * 32 + x, region.region_z * 32 + z)
                open(chunk_file_path + ".wip", "wb").write(compressed)
                os.utime(chunk_file_path + ".wip", (region.mtime, region.mtime))
                os.rename(chunk_file_path + ".wip", chunk_file_path)

                final_chunk_data = struct.pack(">IB", 1, EXTERNAL_FILE_COMPRESSION_TYPE)
                sector_count = 1
                padding = 4096 - (len(final_chunk_data) % 4096)
                if padding == 4096:
                    padding = 0
                final_chunk_data += b'\x00' * padding
            sectors.append(final_chunk_data)
            free_sector += sector_count
        else:
            sectors.append(b'')

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        if region.chunks[i] != None:
            sector_count = len(sectors[i]) // 4096
            header_chunks.append(struct.pack(">IB", start_sectors[i], sector_count)[1:])
        else:
            header_chunks.append(b"\x00\x00\x00\x00")

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        header_timestamps.append(struct.pack(">I", region.timestamps[i]))

    with open(destination_filename + ".wip", "wb") as f:
        f.write(b''.join(header_chunks) + b''.join(header_timestamps) + b''.join(sectors))
        f.flush()
        os.fsync(f.fileno()) # Ensure atomicity on Btrfs
    os.utime(destination_filename + ".wip", (region.mtime, region.mtime))
    os.rename(destination_filename + ".wip", destination_filename)


def write_region_anvil_to_bytes(region: Region, compression_level=zlib.Z_DEFAULT_COMPRESSION): # CAREFUL: Doesn't support MCC!
    SECTOR = 4096

    header_chunks = []
    header_timestamps = []
    sectors = []
    start_sectors = []
    free_sector = 2

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        start_sectors.append(free_sector)
        if region.chunks[i] != None:
            compressed = zlib.compress(region.chunks[i].raw_chunk, compression_level)
            final_chunk_data = struct.pack(">I", len(compressed) + 1) + COMPRESSION_TYPE + compressed

            padding = 4096 - (len(final_chunk_data) % 4096)
            if padding == 4096:
                padding = 0
            final_chunk_data += b'\x00' * padding

            sector_count = len(final_chunk_data) // 4096
            sectors.append(final_chunk_data)
            free_sector += sector_count
        else:
            sectors.append(b'')

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        if region.chunks[i] != None:
            sector_count = len(sectors[i]) // 4096
            header_chunks.append(struct.pack(">IB", start_sectors[i], sector_count)[1:])
        else:
            header_chunks.append(b"\x00\x00\x00\x00")

    for i in range(REGION_DIMENSION * REGION_DIMENSION):
        header_timestamps.append(struct.pack(">I", region.timestamps[i]))

    return b''.join(header_chunks) + b''.join(header_timestamps) + b''.join(sectors)
