#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging
import datetime
import os

from errno import EACCES
from os.path import realpath
from threading import Lock

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from azure.storage.common import CloudStorageAccount

class Loopback(LoggingMixIn, Operations):
    def __init__(self, root, csa, containername):
        self.root = realpath(root)
        self.rwlock = Lock()
        self.account = csa
        self.service = self.account.create_block_blob_service()
        self.defaultContainer = containername

        self.lastreadblobs = [];
        self.lastreadblobpaths = [];
        self.pathswritten = []

    def __call__(self, op, path, *args):
        return super(Loopback, self).__call__(op, path.strip('/').strip('.').strip('_'), *args)

    def getcachepath(self, path):
        return self.root + "/" + path

    def access(self, path, mode):
        print("access " + path)
        if self.lastreadblobpaths == []:
            print("access because lastreadblobpaths empty")
            return

        if path in self.lastreadblobpaths:
            print("access is in lastreadblobpaths")
            return

        # if in cache
        if os.access(self.getcachepath(path), mode):
            print("access is in cache")
            return

        print("access error")
        raise FuseOSError(EACCES)

    def chmod(self, path, mode):
        print("chmod")
        return os.chmod(self.getcachepath(path), mode)

    def chown(self, path, uid, gid):
        print("chown")
        return os.chown(self.getcachepath(path), uid, gid)

    def create(self, path, mode):
        print("create " + path);
        self.service.create_blob_from_text(self.defaultContainer, path, u'')
        return os.open(self.getcachepath(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)

    def flush(self, path, fh):
        print("flush")
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        print("fsync " + path)
        return os.fsync(fh)
        #
        # if datasync != 0:
        #     return os.fdatasync(fh)
        # else:
        #     return os.fsync(fh)

    def getattr(self, path, fh=None):
        print("getattr " + path)

        if os.path.exists(self.getcachepath(path)):
            print("getattr from cache")
            st = os.lstat(self.getcachepath(path))
            return dict((key, getattr(st, key)) for key in (
                'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
                'st_nlink', 'st_size', 'st_uid'))
        else:
            # get from blob
            filefound = next((x for x in self.lastreadblobs if x.name == path), {})
            if filefound != {}:
                content_length = filefound.properties.content_length
                last_modified = filefound.properties.last_modified.timestamp()
                creation_time = filefound.properties.creation_time.timestamp()

                b = {"st_atime": 1539150234.3898132, 'st_ctime' : creation_time, 'st_gid': 20, 'st_mode': 33261,
                     'st_mtime': last_modified, 'st_nlink': 1, 'st_size': content_length, 'st_uid': 501}

                return b

            # return dummy stuff
            st = os.lstat(self.getcachepath(path))
            return dict((key, getattr(st, key)) for key in (
                'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
                'st_nlink', 'st_size', 'st_uid'))

    getxattr = None

    def link(self, target, source):
        print("link")
        return os.link(self.root + source, target)

    listxattr = None

    def mkdir(self, path, mode):
        print("mkdir")
        return os.mkdir(self.getcachepath(path), mode)

    def mknod(self, path, mode, dev):
        print("mknod")
        return os.mknod(self.getcachepath(path), mode, dev)

    def open(self, path, flags):
        print("open " + path)

        # check cache
        if os.path.exists(self.getcachepath(path)):
            print("file is in cache")
            return os.open(self.getcachepath(path), flags)
        else:
            print("file not in cache " + self.getcachepath(path))
            self.service.get_blob_to_path(self.defaultContainer, path, self.getcachepath(path))
            return os.open(self.getcachepath(path), flags)

    def read(self, path, size, offset, fh):
        print("read " + path)
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        # check cache
        if self.lastreadblobpaths != [] and os.path.exists(self.getcachepath(path)):
            print("readdir is in cache")
            return ['.', '..', ] + os.listdir(self.getcachepath(path))
        else:
            print('readdir ' + path)
            blobs = list(self.service.list_blobs(self.defaultContainer, prefix=path))
            self.lastreadblobs = blobs
            self.lastreadblobpaths = [x.name for x in blobs];
            # for blob in blobs:
                # print(blob.name)  # blob1, blob2

            return ['.', '..'] + self.lastreadblobpaths;

    def readlink(self, path):
        print("readlink")
        return os.readlink(self.getcachepath(path))

    def release(self, path, fh):
        print("release")
        if path in self.pathswritten:
            self.service.create_blob_from_path(self.defaultContainer, path, self.getcachepath(path))
            self.pathswritten.remove(path)

        return os.close(fh)

    def rename(self, old, new):
        print("rename")
        return os.rename(old, self.root + new)

    def rmdir(self, path):
        print("rmdir")
        return os.rmdir(self.getcachepath(path))

    def statfs(self, path):
        print("statfs " + path)
        stv = os.statvfs(self.getcachepath(path))
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
            'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'))

    def symlink(self, target, source):
        print("symlink")
        return os.symlink(source, target)

    def truncate(self, path, length, fh=None):
        print("truncate")
        with open(self.getcachepath(path), 'r+') as f:
            f.truncate(length)

    def unlink(self, path):
        print("unlink " + path)
        self.service.delete_blob(self.defaultContainer, path)
        return os.unlink(self.getcachepath(path))

    def utimens(self, path, times=None):
        print("utimens " + path)
        return os.utime(self.getcachepath(path), times)

    def write(self, path, data, offset, fh):
        print("write " + path);
        self.pathswritten.append(path)
        result = -1;
        with self.rwlock:
            os.lseek(fh, offset, 0)
            result = os.write(fh, data)
        return result


if __name__ == '__main__':
    import json

    with open('creds.json', 'r') as f:
        creds = json.load(f)
    csa = CloudStorageAccount(account_name=creds["accountname"], account_key=creds["accountkey"])
    containername = creds["containername"]
    mount = creds["mount"]
    cache = creds["cache"]

    logging.basicConfig(level=logging.ERROR)
    fuse = FUSE(
        Loopback(cache, csa, containername), mount, foreground=True, allow_other=True)

    # use this for debugging.
    # logging.basicConfig(level=logging.ERROR)
    # lp = Loopback("cache", csa)
    # lp.readdir("", "as")
    # lp.getattr("xp.txt")