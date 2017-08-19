import os


def fnd(f, s, start=0):
    fsize = f.seek(0, os.SEEK_END)
    f.seek(0)
    bsize = 4096
    buffer = None
    if start > 0:
        f.seek(start)
    overlap = len(s) - 1
    while True:
        if overlap <= f.tell() < fsize:
            f.seek(f.tell() - overlap)
        buffer = f.read(bsize)
        if buffer:
            pos = buffer.find(s)
            if pos >= 0:
                return f.tell() - (len(buffer) - pos)
        else:
            return -1


def fnd_all(f, s):
    results = []
    last_addr = -len(s)
    while True:
        addr = fnd(f, s, start=last_addr + len(s))
        if addr != -1:
            results.append(addr)
            last_addr = addr
        else:
            return results
