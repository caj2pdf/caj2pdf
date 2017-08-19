import struct


class CAJParser(object):
    def __init__(self, filename):
        self.filename = filename
        self.__PAGE_NUMBER_OFFSET = 0x10
        self.__TOC_NUMBER_OFFSET = 0x110

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
