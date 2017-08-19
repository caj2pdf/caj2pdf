import struct


class Parser(object):
    def __init__(self, filename):
        self.filename = filename
        with open(filename, "rb") as caj:
            fmt = struct.unpack("4s", caj.read(4))[0].replace(b'\x00', b'').decode("gb2312")
        if fmt == "CAJ":
            self.__PAGE_NUMBER_OFFSET = 0x10
            self.__TOC_NUMBER_OFFSET = 0x110
        elif fmt == "HN":
            self.__PAGE_NUMBER_OFFSET = 0x90
            self.__TOC_NUMBER_OFFSET = 0x158

    @property
    def page_num(self):
        with open(self.filename, "rb") as caj:
            caj.seek(self.__PAGE_NUMBER_OFFSET)
            [page_num] = struct.unpack("i", caj.read(4))
            return page_num

    @property
    def toc_num(self):
        with open(self.filename, "rb") as caj:
            caj.seek(self.__TOC_NUMBER_OFFSET)
            [toc_num] = struct.unpack("i", caj.read(4))
            return toc_num


class CAJParser(Parser):
    pass


class HNParser(Parser):
    pass
