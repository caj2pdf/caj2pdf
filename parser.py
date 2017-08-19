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

    def get_toc(self):
        toc = []
        with open(self.filename, "rb") as caj:
            for i in range(self.toc_num):
                caj.seek(self.__TOC_NUMBER_OFFSET + 4 + 0x134 * i)
                toc_bytes = struct.unpack("256s24s12s12si", caj.read(0x134))
                title = toc_bytes[0].replace(b'\x00', b'').decode("gb2312").encode("utf-8")
                page = int(toc_bytes[2].replace(b'\x00', b''))
                level = toc_bytes[4]
                toc_entry = {"title": title, "page": page, "level": level}
                toc.append(toc_entry)
        return toc

    def output_toc(self, dest):
        toc_items = self.get_toc()
        with open(dest, "wb") as f:
            for toc in toc_items:
                f.write(b'    ' * (toc["level"] - 1) + toc["title"]
                        + b'    ' + str(toc["page"]).encode("utf-8") + b'\n')


class CAJParser(Parser):
    pass


class HNParser(Parser):
    pass
