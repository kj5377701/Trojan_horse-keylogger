import socket
import struct
import io
import os
import time
import shutil
from inout import *
import logging

FILE_SUCCESS_TAG = B'FILEGOOD'
FILE_FAIL_TAG = B'FILEFAIL'
FILE_ABORT_TAG = B'FILEABRT'
FILE_BEGIN_TAG = B'FILEBEG0'
FILE_END_TAG = B'FILEEND0'
FILE_SIZE_TAG = B'FILESIZE'
FILE_NAME_TAG = B'FILENAME'
FILE_CONTENT_TAG = B'FILEDATA'
FILE_BLOCK_TAG = b'FILEBLKS'
FILE_TAG_SIZE = len(FILE_SIZE_TAG)


class NetAPI():
    def __init__(self, iHandle=None, oHandle=None):
        if not iHandle:
            iHandle = b''
        if not oHandle:
            oHandle = iHandle
        self.iHandle = InitIO(iHandle)
        self.oHandle = InitIO(oHandle)
        self.save_path = '/home/kj5377701/PycharmProjects/Trojan_horse/save_file/'
        self.max_size = 2147483647
        self.block_size = 4096

    def recv_file(self):
        receiver = {FILE_NAME_TAG: self.recv_name,
                    FILE_SIZE_TAG: self.recv_size,
                    FILE_CONTENT_TAG: self.recv_content,
                    FILE_BLOCK_TAG: self.recv_blocks,
                    }
        while 1:
            tag = None
            logging.debug('wait for tag')
            try:
                data = self.recv_data()
                if data is None:
                    break
                continue
            except InOutException as e:
                tag = e.args[0]
            except socket.error:
                logging.error('Exception: %s' % str(e))
                raise
            except Exception as e:
                logging.error('Exception: %s' % str(e))
                break
            logging.debug('get tag: %s' % tag)
            if not tag:
                continue
            elif tag == FILE_BEGIN_TAG:
                result = {}
                logging.debug('sending success after get tag')
                self.send_success()
                continue
            elif tag == FILE_END_TAG:
                logging.debug('send success after get tag')
                self.send_success()
                break
            elif tag == FILE_ABORT_TAG:
                logging.debug('abort')
                result = {}
                continue
            self.send_success()
            try:
                logging.debug('wait for receive data')
                data = receiver.get(tag, None)()
                if data is None:
                    break
                result[tag] = data
                logging.debug('send success after receive data')
                self.send_success()
                continue
            except InOutException as e:
                tag = e.args[0]
                break
            except socket.error:
                raise
            except Exception as e:
                logging.error('Exception: %s' % str(e))
                break
            logging.debug('send fail after data')
            self.send_fail()
        if not result:
            result = None
        return result

    def send_file(self, path):
        filename = os.path.abspath(path)
        filesize = os.path.getsize(path)
        try:
            logging.debug('test for: %s' % filename)
            open(filename, 'rb')
        except Exception as e:
            logging.error('Exception while testing opening: %s %s' % filename, str(e))
            return None
        if filesize > self.block_size:
            filetag, filesend = (FILE_BLOCK_TAG, lambda: self.send_blocks(path))
        else:
            filetag, filesend = (FILE_CONTENT_TAG, lambda: self.send_content(path))
        fileInfo = [
            (FILE_BEGIN_TAG, None),
            (FILE_NAME_TAG, lambda: self.send_name(filename)),
            (FILE_SIZE_TAG, lambda: self.send_size(filesize)),
            (filetag, filesend),
            (FILE_END_TAG, None)
        ]
        for tag, sendaction in fileInfo:
            backtag = None
            error = None
            try:
                self.send_tag(tag)
                logging.debug('waiting for response after send tag %s' % tag)
                self.recv_data()
            except InOutException as e:
                logging.error('get tag %s' % e.args[0])
                backtag = e.args[0]
            except socket.error as e:
                logging.error('exception when send tag: %s %s' % (tag, str(e)))
                error = FILE_ABORT_TAG
                break
            if error:
                self.send_tag(error)
                return False
            error = None
            if not sendaction:
                continue
            try:
                sendaction()
                logging.debug('wait for response after action')
                self.recv_data()
            except InOutException as e:
                logging.info('Exception when send action: %s %s ')
                backtag = e.args[0]
            except Exception as e:
                logging.error('Exception: %s' % str(e))
                error = FILE_ABORT_TAG
                break
            if error:
                self.send_tag(error)
            if backtag != FILE_SUCCESS_TAG:
                return False
        return True

    def recv_tag(self):
        return self.iHandle.read()

    def recv_data(self):
        return self.iHandle.read()

    def send_tag(self, tag):
        self.oHandle.write(tag)

    def send_data(self, data):
        self.oHandle.write(data)

    def send_size(self, n):
        return self.send_data(n)

    def send_name(self, s):
        return self.send_data(s)

    def send_content(self, d):
        return self.send_data(d)

    def send_blocks(self, filename):
        fp = open(filename, 'rb')
        block_id = 0
        total_size = 0
        while 1:
            block = fp.read(self.block_size)
            if not block:
                break
            block_id += 1
            self.send_data(block_id)
            self.send_data(block)
            total_size += len(block)
            backID = self.recv_data()
            if backID != block_id:
                self.send_fail()
                break
        self.send_data(0)
        return total_size

    def recv_size(self):
        size = self.recv_data()
        if not isinstance(size, int):
            raise TypeError('the size is not int')
        return size

    def recv_name(self):
        path = self.recv_data()
        if not isinstance(path, str):
            raise TypeError('the path is not type str')
        namelist = path.split('\t')
        if '..' in namelist:
            raise ValueError('dangerous path!')
        name = os.path.join(*namelist)
        return name

    def recv_content(self):
        return self.recv_data()

    def recv_blocks(self):
        total_size = 0
        last_block_id = 0
        filename = os.path.abspath(os.path.join(self.save_path, 'TEMP%x' % int(time.time())))
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'wb') as fp:
            while 1:
                block_id = self.recv_data()
                if not isinstance(block_id, int):
                    raise TypeError('invalid type of block id')
                if block_id == 0:
                    break
                if last_block_id + 1 != block_id:
                    raise ValueError('block id error last')
                last_block_id = block_id
                block = self.recv_data()
                if not isinstance(block, bytes):
                    raise TypeError('invalid type of block')
                if len(block) + total_size > self.max_size:
                    raise RuntimeError('exceed max file size limit')
                fp.write(block)
                self.send_data(block_id)
                total_size += len(block)
        return filename

    def send_success(self):
        self.send_tag(FILE_SUCCESS_TAG)

    def send_fail(self):
        self.send_tag(FILE_FAIL_TAG)

    def send_abort(self, n):
        self.send_tag(FILE_ABORT_TAG)


def save_file(fileInFo, target):
    filename = fileInFo.get(FILE_NAME_TAG)
    filesize = fileInFo.get(FILE_SIZE_TAG)
    content = fileInFo.get(FILE_CONTENT_TAG)
    tempfile = fileInFo.get(FILE_BLOCK_TAG)
    if not filename or not filesize:
        return False
    if content or tempfile:
        fullname = os.path.join(target, filename)
        dirname = os.path.dirname(fullname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if content:
            if len(content) != filesize:
                raise ValueError('size unmatched')
            with open(fullname, 'wb') as fp:
                fp.write(content)
        else:
            if os.path.getsize(tempfile) != filesize:
                raise RuntimeError('size unmatched')
            shutil.move(tempfile, fullname)
        return True
    else:
        return False
