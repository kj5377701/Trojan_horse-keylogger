import os
import stat
import platform


def split_path(path):
    result = []
    while 1:
        head, tail = os.path.split(path)
        if tail:
            result.insert(0, tail)
            path = head
        else:
            head = head.strip('/:\\')
            if head:
                result.insert(0, head)
            break
    return result


def scan_dir(path):
    if os.path.isdir(path):
        for name in os.listdir(path):
            fullpath = os.path.join(path, name)
            yield from scan_dir(fullpath)
    else:
        yield path


windos = ['C:\\Users', 'D:', 'E:', 'F']
linux = ['/root', '/home', '/etc']

all_start_dirs = {'Windos': windos,
                  'Linux': linux}
start_dirs = all_start_dirs.get(platform.system(), None)

for path in [p for p in start_dirs if os.path.exists(p)]:
    for filename in scan_dir(path):
        print(filename)
