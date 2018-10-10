#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging
import os

from errno import EACCES
from os.path import realpath
from threading import Lock

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from azure.storage.common import CloudStorageAccount

class Loopback(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = realpath(root)
        self.rwlock = Lock()
        self.account = CloudStorageAccount(account_name="",
                                           account_key="")
        self.service = self.account.create_block_blob_service()
        self.defaultContainer = "default"

    def __call__(self, op, path, *args):
        return super(Loopback, self).__call__(op, path.strip('/').strip('.').strip('_'), *args)

    def getcachepath(self, path):
        return self.root + "/" + path

    def access(self, path, mode):
        print("access " + path)
        if not os.access(self.getcachepath(path), mode):
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
        # st = os.lstat(self.getcachepath(path))
        # print(st)

        # b = dict((key, getattr(st, key)) for key in (
        #     'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
        #     'st_nlink', 'st_size', 'st_uid'))


        b = {"st_atime": 1539150234.3898132, 'st_ctime' : 1539147774.3190603, 'st_gid': 20, 'st_mode': 16877,
             'st_mtime': 1539147774.3190603, 'st_nlink': 3, 'st_size': 96, 'st_uid': 5011}

        return b

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
        return os.open(self.getcachepath(path), flags)

    def read(self, path, size, offset, fh):
        print("read " + path)
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)

    def readdir(self, path, fh):
        print('readdir ' + path)
        blobs = list(self.service.list_blobs(self.defaultContainer, prefix=path))
        # for blob in blobs:
            # print(blob.name)  # blob1, blob2

        return ['.', '..'] + [x.name for x in blobs];
        # x = ['.', '..', ] + os.listdir(self.getcachepath(path)) # for cache

    def readlink(self, path):
        print("readlink")
        return os.readlink(self.getcachepath(path))

    def release(self, path, fh):
        print("release")
        self.service.create_blob_from_path(self.defaultContainer, path, self.getcachepath(path))
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
        result = -1;
        with self.rwlock:
            os.lseek(fh, offset, 0)
            result = os.write(fh, data)
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('cache')
    parser.add_argument('mount')
    args = parser.parse_args()
    logging.basicConfig(level=logging.ERROR)
    fuse = FUSE(
        Loopback(args.cache), args.mount, foreground=True, allow_other=True)

    # args = { }
    # args["cache"] = "cache"
    # args["mount"] = "mount"
    # logging.basicConfig(level=logging.ERROR)
    # fuse = FUSE(
    #     Loopback(args["cache"]), args["mount"], foreground=True, allow_other=True)

    # lp = Loopback("cache")
    # lp.readdir("", "as")
    # lp.getattr("")