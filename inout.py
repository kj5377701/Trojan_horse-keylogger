import socket
import struct
import io


class INOUT():
    def __init__(self, handle):
        self.handle = handle

    def data_to_nbyte(self, n):
        if isinstance(n, int):
            if n < (1 << 8):
                tag = 'B'
            elif n < (1 << 16):
                tag = 'H'
            elif n < (1 << 32):
                tag = 'L'
            else:
                tag = 'Q'
            n = struct.pack('!' + tag, n)
            return tag.encode('utf-8') + n
        elif isinstance(n, str):
            tag = 'c'
            n = n.encode('utf-8')
            return tag.encode('utf-8') + self.data_to_nbyte(len(n)) + n
        elif isinstance(n, bytes):
            tag = 's'
            return tag.encode('utf-8') + self.data_to_nbyte(len(n)) + n
        raise TypeError('invalid type: ' + type(n))

    def nbyte_to_data(self):
        size_info = {'B': 1, 'H': 2, 'L': 4, 'Q': 8}
        btag = self.read_raw(1)

        if not btag:
            return None

        tag = btag.decode('utf-8')

        if tag in size_info:
            size = size_info[tag]
            bnum = self.read_raw(size)
            result = struct.unpack('!' + tag, bnum)[0]
        elif tag in ['s', 'c']:
            size = self.nbyte_to_data()
            if size >= 65536:
                raise ValueError('length too long')
            # here we plus a while to prevent the data from lose(because in socket, data could loose during send)
            bstr = b''
            while len(bstr) < size:
                bstr += self.read_raw(size - len(bstr))
            result = bstr if tag == 's' else bstr.decode('utf-8')
        return result

    def read(self):
        return self.nbyte_to_data()

    def write(self, d):
        byte_data = self.data_to_nbyte(d)
        self.write_raw(byte_data)

    def close(self):
        return self.close_handle()

    def read_handle(self, n):
        return b''

    def write_handle(self, d):
        print(d)
        return len(d)

    def read_raw(self, n):
        return self.read_handle(n)

    def write_raw(self, d):
        return self.write(d)

    def close_handle(self):
        return self.handle


class NetworkIO(INOUT):
    def read_handle(self, n):
        return self.handle.recv(n)

    def write_handle(self, d):
        return self.handle.send(d)


class FileIO(INOUT):
    def read_handle(self, n):
        return self.handle.read(n)

    def write_handle(self, d):
        return self.handle.write(d)


class StringIO(INOUT):
    def read_handle(self, n):
        data, self.handle = self.handle[:n], self.handle[n:]
        return data

    def write_handle(self, d):
        self.handle += d


def InitIO(handle):
    readers = {
        bytes: StringIO,
        io.IOBase: FileIO,
        socket.socket: NetworkIO
    }
    return readers.get(type(handle), None)(handle)
