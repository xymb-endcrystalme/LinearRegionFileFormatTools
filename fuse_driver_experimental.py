#!/usr/bin/env python

# This code is based on https://github.com/skorokithakis/python-fuse-sample

# Copyright (c) 2016, Stavros Korokithakis & Xymb
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import errno
import time
import zlib

from fuse import FUSE, FuseOSError, Operations, fuse_get_context
from collections import OrderedDict
from linear import open_region_linear, write_region_anvil_to_bytes

MCA_FILES_SIZE = 20 * 1024 * 1024

class LinearFileCache:
    FILE_DESCRIPTOR_THRESHOLD = 1000

    def __init__(self, cache_size):
        self.cache_size = cache_size
        self.cache = OrderedDict()
        self.file_references = {}
        self.file_handle_to_path = {}
        self.next_file_handle = self.FILE_DESCRIPTOR_THRESHOLD

    def create_file(self, path_linear):
#        region = open(path_linear, "rb").read()
#            content = file.read()
        start = time.time()
        region = open_region_linear(path_linear)
        retval = write_region_anvil_to_bytes(region, compression_level=zlib.Z_BEST_SPEED)
        print("GENERATING ", len(retval), path_linear, (time.time() - start)*1000, "ms")
        return retval
        # Create a 10MB bytes array
#        content = bytearray(10 * 1024 * 1024)
        # Cache the bytes array
#        return bytes(content)
#        return linear

    def open(self, path_linear):
        if not os.path.isfile(path_linear):
            raise FileNotFoundError(f"File {path_linear} does not exist.")

        print("Found", path_linear in self.cache)
        print("Cache contents:", self.cache.keys())
        if path_linear not in self.cache:
            if len(self.cache) >= self.cache_size:
                oldest_file_path, _ = self.cache.popitem(last=False)
                self.file_references.pop(oldest_file_path)

            self.cache[path_linear] = self.create_file(path_linear)
            self.file_references[path_linear] = 0

        self.file_references[path_linear] += 1
        file_handle = self.next_file_handle
        self.next_file_handle += 1
        self.file_handle_to_path[file_handle] = path_linear

        return file_handle

    def close(self, file_handle):
        if file_handle in self.file_handle_to_path:
            path_linear = self.file_handle_to_path[file_handle]
            self.file_references[path_linear] -= 1

            if self.file_references[path_linear] == 0 and len(self.cache) >= self.cache_size:
                self.cache.pop(path_linear)
                self.file_references.pop(path_linear)

            self.file_handle_to_path.pop(file_handle)

    def read(self, file_handle, length, offset):
        if file_handle in self.file_handle_to_path:
            path_linear = self.file_handle_to_path[file_handle]

            if path_linear in self.cache:
                file_data = self.cache[path_linear]
#                print("aaa", len(file_data))
#                print(f"Read {length} bytes from {path_linear} at offset {offset}.")#, file_data[offset:offset + length])
                return file_data[offset:offset + length]
            else:
                raise FileNotFoundError(f"File {path_linear} not found in cache.")
        else:
            raise ValueError(f"Invalid file handle {file_handle}.")
'''
class LinearFileCache:
    def __init__(self, cache_size):
        self.cache = {}
        self.cache_size = cache_size
        self.open_files = {}

    def open(self, path_linear):
        if path_linear in self.open_files:

        pass
'''

class LinearToMCA(Operations):
    def __init__(self, root, linear_file_cache):
        self.root = root
        self.linear_file_cache = linear_file_cache

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path
    
    def access(self, path, mode):
        return
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        return
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        return
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
#        print("getattr called with path: " + path)
        full_path = self._full_path(path)
        if path.endswith(".mca"):
            real_file = full_path[:-4] + ".linear"
            st = os.lstat(real_file)
            retval = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
            retval["st_size"] = MCA_FILES_SIZE
            return retval
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            files = os.listdir(full_path)
            final_files = []
            for f in files:
                file = f
                if f.endswith(".linear"):
                    file = f[:-7] + ".mca"
                if f.endswith(".linear.tmp"):
                    continue
                final_files.append(file)
            dirents.extend(final_files)
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        return
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        print("statfs called with path: " + path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return
        return os.symlink(target, self._full_path(name))

    def rename(self, old, new):
        return
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return
        return os.link(self._full_path(name), self._full_path(target))

    def utimens(self, path, times=None):
        return
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        print("open called with path: " + path)
        start = time.time()
        full_path = self._full_path(path)
#        return os.open(full_path, flags)

        if path.endswith(".mca"):
            real_file = full_path[:-4] + ".linear"
            file_handle = self.linear_file_cache.open(real_file)
#            print("file_handle:", file_handle)
            print("open time:", time.time() - start)
            return file_handle

        retval = os.open(full_path, flags)
#        print(retval, flags)
        return retval

    def create(self, path, mode, fi=None):
        return
        uid, gid, pid = fuse_get_context()
        full_path = self._full_path(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid
        return fd

    def read(self, path, length, offset, fh):
#        print("read called with path:", path, "length:", length, "offset:", offset, "fh:", fh)
        start = time.time()
        if path.endswith(".mca"):
            retval = self.linear_file_cache.read(fh, length, offset)
#            print("read retval:", retval)
            #print("read time:", time.time() - start)
            return retval
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)
        return 

    def write(self, path, buf, offset, fh):
        return
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return
        print("flush called with path: " + path + " fh: " + str(fh))
        retval = os.fsync(fh)
        print("RETVAL flush ", retval)
        return retval

    def release(self, path, fh):
        print("release called with path: " + path + " fh: " + str(fh))
        if path.endswith(".mca"):
            retval = self.linear_file_cache.close(fh)
            print("RETVAL ", retval)
            return retval
        retval = os.close(fh)
        print("RETVAL ", retval)
        return retval

    def fsync(self, path, fdatasync, fh):
        return
        print("fsync called with path: " + path + " fdatasync: " + str(fdatasync) + " fh: " + str(fh))
        return self.flush(path, fh)

def main(mountpoint, root):
    linear_file_cache = LinearFileCache(100)
#    FUSE(LinearToMCA(root, linear_file_cache), mountpoint, nothreads=True, foreground=True, allow_other=False, ro=True)
    FUSE(LinearToMCA(root, linear_file_cache), mountpoint, nothreads=True, foreground=True, allow_other=False, ro=False)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
'''
import argparse

def main():
    parser = argparse.ArgumentParser(description="Fuse program for mounting a read-only file system. The program doesn't support writing files, only reading them.")

    parser.add_argument("server_directory", type=str, help="Server directory to be mounted")
    parser.add_argument("mountpoint", type=str, help="Mount point for the server directory")

    parser.add_argument("-b", "--background", action="store_true", default=False, help="Run the program in the background (default: off)")
    parser.add_argument("-a", "--allow_other", action="store_true", default=False, help="Allow other users to access the mounted directory (default: off)")
    parser.add_argument("-c", "--cache_size", type=int, default=100, help="Cache size (default: 100)")

    args = parser.parse_args()

    # Your Fuse program implementation here
    # Example: mount_fuse(args.server_directory, args.mountpoint, args.background, args.allow_other, args.cache_size)

if __name__ == "__main__":
    main()
'''