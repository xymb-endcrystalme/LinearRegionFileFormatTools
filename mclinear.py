import os
import struct
import pyzstd
import zlib
import nbtlib
import io
import xxhash

class Chunk:
    def __init__(self, raw_chunk, x, z):
        self.raw_chunk = raw_chunk
        self.x, self.z = x, z

    def as_nbtlib(self):
        fileobj = io.BytesIO(self.raw_chunk)
        file = nbtlib.File.parse(fileobj)
        return file

    def from_nbtlib(self, nbtlib_obj):
        fileobj = io.BytesIO()
        nbtlib_obj.write(fileobj)
        self.raw_chunk = fileobj.getvalue()

    def __str__(self):
        return "Chunk %d %d - %d bytes" % (self.x, self.z, len(self.raw_chunk))

class Region:
    def __init__(self, chunks, region_x, region_z, mtime, timestamps, nbt_features={}):
        self.chunks = chunks
        self.region_x, self.region_z = region_x, region_z
        self.mtime = mtime
        self.timestamps = timestamps
        self.nbt_features = nbt_features

    def chunk_count(self):
        count = 0
        for i in self.chunks:
            count += 1
        return count

    def __str__(self):
        non_empty_chunks = sum(1 for chunk in self.chunks if chunk is not None)
        return f"Region ({self.region_x}, {self.region_z}) - {non_empty_chunks}/{len(self.chunks)} chunks - Last modified: {self.mtime}"

REGION_DIMENSION = 32
COMPRESSION_TYPE = b'\x02'
COMPRESSION_TYPE_ZLIB = 2
EXTERNAL_FILE_COMPRESSION_TYPE = 128 + 2
LINEAR_SIGNATURE = 0xc3ff13183cca9d9a

# TODO: Alert users if the file name isn't r.0.0.linear

def open_region_linear(file_path):
    SUPPORTED_VERSION = [1, 2]

    HEADER_SIZE = REGION_DIMENSION * REGION_DIMENSION * 8

    file_coords = file_path.split('/')[-1].split('.')[1:3]
    region_x, region_z = int(file_coords[0]), int(file_coords[1])

    with open(file_path, 'rb') as f:
        raw_region = f.read()
    mtime = os.path.getmtime(file_path)

    signature, version, newest_timestamp, compression_level, chunk_count, complete_region_length, reserved = struct.unpack_from(">QBQbhIQ", raw_region, 0)

    if signature != LINEAR_SIGNATURE:
        raise Exception("Superblock invalid")
    if version not in SUPPORTED_VERSION:
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
        with open(file_path, 'rb') as f:
            raw_region = f.read()
    except FileNotFoundError: return False
    mtime = os.path.getmtime(file_path)

    signature, version, newest_timestamp, compression_level, chunk_count, complete_region_length, hash64 = struct.unpack_from(">QBQbhIQ", raw_region, 0)

    if signature != LINEAR_SIGNATURE:
        return False
    if version not in SUPPORTED_VERSION:
        return False

    signature = struct.unpack(">Q", raw_region[-8:])[0]

    if signature != LINEAR_SIGNATURE:
        return False

    return True

def write_region_linear(destination_filename, region: Region, compression_level=1):
    LINEAR_VERSION = 1
    inside_header = []
    newest_timestamp = 0
    chunk_count = 0

    for i in range(32**2):
        if region.chunks[i] != None:
            inside_header.append(struct.pack(">II", len(region.chunks[i].raw_chunk), region.timestamps[i]))
            newest_timestamp = max(region.timestamps[i], newest_timestamp)
            chunk_count += 1
        else:
            inside_header.append(struct.pack(">II", 0, region.timestamps[i]))

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
    with open(file_path, 'rb') as f: anvil_file = f.read()

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

def serialize_existence_bitmap(bitmap):
    result = bytearray()
    for i in range(0, len(bitmap), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bitmap) and bitmap[i + j]:
                byte |= (1 << (7 - j))
        result.append(byte)
    return bytes(result)

def deserialize_existence_bitmap(serialized_bitmap):
    result = []
    for byte in serialized_bitmap:
        for i in range(8):
            result.append(bool(byte & (1 << (7 - i))))
    return result[:1024]

def write_dict_to_bytes(data):
    result = bytearray()
    for key, value in data.items():
        key_bytes = key.encode('utf-8')
        if len(key_bytes) > 255:
            raise ValueError(f"String '{key}' is longer than 255 bytes")
        result.append(len(key_bytes))
        result.extend(key_bytes)
        result.extend(struct.pack(">I", value))
    result.append(0)
    return bytes(result)

def read_dict_from_bytes(data):
    result = {}
    i = 0
    while True:
        key_length = data[i]
        if key_length == 0:
            return result, i + 1
        i += 1
        key = data[i:i + key_length].decode('utf-8')
        i += key_length
        value = struct.unpack(">I", data[i:i + 4])[0]
        i += 4
        result[key] = value

def write_region_linear_v2(destination_filename, region: Region, compression_level=1, grid_size=8):
    LINEAR_VERSION = 3

    if grid_size not in [1, 2, 4, 8, 16, 32]: raise Exception("Incorred grid_size %d" % (grid_size))
    newest_timestamp = 0

    chunks = [[None for _ in range(32)] for _ in range(32)]
    buckets = [[[] for _ in range(grid_size)] for _ in range(grid_size)]
    chunk_existence_bitmap = [False] * 1024

    for i in range(32**2):
        x = i % 32
        z = i // 32
        if region.chunks[i] is not None:
            chunks[x][z] = struct.pack(">IQ", len(region.chunks[i].raw_chunk) + 8, region.timestamps[i]) + region.chunks[i].raw_chunk
            chunk_existence_bitmap[i] = True
            newest_timestamp = max(region.timestamps[i], newest_timestamp)
        else:
            chunks[x][z] = struct.pack(">IQ", 0, region.timestamps[i])

    for x in range(grid_size):
        for z in range(grid_size):
            bucket = buckets[x][z]
            for ix in range(32 // grid_size):
                for iz in range(32 // grid_size):
                    bucket.append(chunks[x * (32 // grid_size) + ix][z * (32 // grid_size) + iz])

    chunk_existence_bitmap = serialize_existence_bitmap(chunk_existence_bitmap)

    option = {pyzstd.CParameter.compressionLevel: compression_level,
              pyzstd.CParameter.checksumFlag: 1}
    buckets_str = []
    for x in range(grid_size):
        for z in range(grid_size):
            complete_subregion = b"".join(buckets[x][z])
            if len(complete_subregion) == 64:
                buckets_str.append(b"")
            else:
                complete_subregion = pyzstd.compress(complete_subregion, level_or_option=option)
                buckets_str.append(complete_subregion)

    bucket_sizes = []
    for i in range(len(buckets_str)):
        hash = xxhash.xxh64()
        hash.update(buckets_str[i])
        bucket_sizes.append(struct.pack(">Ib", len(buckets_str[i]), compression_level) + hash.digest())

    bucket_sizes_str = b"".join(bucket_sizes)
    buckets_str = b"".join(buckets_str)

    preheader = struct.pack(">QBQbii", LINEAR_SIGNATURE, LINEAR_VERSION, newest_timestamp, grid_size, region.region_x, region.region_z)
    footer = struct.pack(">Q", LINEAR_SIGNATURE)

    nbt_features = write_dict_to_bytes(region.nbt_features)

    final_region_file = preheader + chunk_existence_bitmap + nbt_features + bucket_sizes_str + buckets_str + footer

    with open(destination_filename + ".wip", "wb") as f:
        f.write(final_region_file)
        f.flush()
        os.fsync(f.fileno()) # Ensure atomicity on Btrfs
    os.utime(destination_filename + ".wip", (region.mtime, region.mtime))
    os.rename(destination_filename + ".wip", destination_filename)


def open_region_linear_v2(file_path):
    LINEAR_VERSION = 3
    with open(file_path, 'rb') as f:
        raw_region = f.read()
    mtime = os.path.getmtime(file_path)

    signature, version, newest_timestamp, grid_size, region_x, region_z = struct.unpack_from(">QBQbii", raw_region, 0)
    if grid_size not in [1, 2, 4, 8, 16, 32]: raise Exception("Incorred grid_size %d" % (grid_size))

    if signature != LINEAR_SIGNATURE:
        raise Exception("Superblock invalid")
    if version != LINEAR_VERSION:
        raise Exception("Version invalid")

    signature = struct.unpack(">Q", raw_region[-8:])[0]

    if signature != LINEAR_SIGNATURE:
        raise Exception("Footer signature invalid")

    offset = 26
    chunk_existence_bitmap = deserialize_existence_bitmap(raw_region[offset:offset + 128])
    offset += 128

    nbt_features, length = read_dict_from_bytes(raw_region[offset:])
    offset += length

    bucket_sizes = []
    for _ in range(grid_size * grid_size):
        bucket_size, compression_level = struct.unpack_from(">Ib", raw_region, offset)
        bucket_hash = raw_region[offset + 5: offset + 13]
        bucket_sizes.append((bucket_size, compression_level, bucket_hash))
        offset += 13

    timestamps = [0 for _ in range(1024)]
    chunks = [None] * REGION_DIMENSION * REGION_DIMENSION
    for x in range(grid_size):
        for z in range(grid_size):
            bucket_size, compression_level, bucket_hash = bucket_sizes[x * grid_size + z]
            if bucket_size > 0:
                compressed_bucket = raw_region[offset:offset + bucket_size]
                decompressed_bucket = pyzstd.decompress(compressed_bucket)
                hash = xxhash.xxh64()
                hash.update(compressed_bucket)
                if bucket_hash != hash.digest(): raise Exception("Bucket hash incorrect! Bitrot?", len(compressed_bucket))
                iterator = 0
                for ix in range(32 // grid_size):
                    for iz in range(32 // grid_size):
                        chunk_index = (x * (32 // grid_size) + ix) + (z * (32 // grid_size) + iz) * 32
                        if True:
                            chunk_size, timestamp = struct.unpack_from(">IQ", decompressed_bucket, iterator)
                            timestamps[chunk_index] = timestamp
                            iterator += 12
                            if chunk_size == 0:
                                if chunk_existence_bitmap[chunk_index] == True: raise Exception("Bitmap is incorrect - false positive")
                                continue
                            if chunk_existence_bitmap[chunk_index] == False:
#                                print("Chunk size", chunk_size)
#                                print("Bitmap is incorrect - false negative", ix, iz)
                                # TODO: Fix
                                raise Exception("Bitmap is incorrect - false negative")
                            chunk_data = decompressed_bucket[iterator:iterator + chunk_size - 8]
                            chunks[chunk_index] = Chunk(chunk_data, REGION_DIMENSION * region_x + chunk_index % 32, REGION_DIMENSION * region_z + chunk_index // 32)
                            iterator += chunk_size - 8
            offset += bucket_size

    return Region(chunks, region_x, region_z, mtime, timestamps, nbt_features=nbt_features)
