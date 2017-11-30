import struct
from subprocess import call
from utils import fnd, fnd_all, add_outlines


class CAJParser(object):
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(filename, "rb") as caj:
                fmt = struct.unpack("4s", caj.read(4))[0].replace(b'\x00', b'').decode("gb18030")
            if fmt == "CAJ":
                self.format = "CAJ"
                self._PAGE_NUMBER_OFFSET = 0x10
                self._TOC_NUMBER_OFFSET = 0x110
            elif fmt == "HN":
                self.format = "HN"
                self._PAGE_NUMBER_OFFSET = 0x90
                self._TOC_NUMBER_OFFSET = 0x158
            else:
                self.format = None
                raise SystemExit("Unknown file type.")
        except UnicodeDecodeError:
            raise SystemExit("Unknown file type.")

    @property
    def page_num(self):
        with open(self.filename, "rb") as caj:
            caj.seek(self._PAGE_NUMBER_OFFSET)
            [page_num] = struct.unpack("i", caj.read(4))
            return page_num

    @property
    def toc_num(self):
        with open(self.filename, "rb") as caj:
            caj.seek(self._TOC_NUMBER_OFFSET)
            [toc_num] = struct.unpack("i", caj.read(4))
            return toc_num

    def get_toc(self):
        toc = []
        with open(self.filename, "rb") as caj:
            for i in range(self.toc_num):
                caj.seek(self._TOC_NUMBER_OFFSET + 4 + 0x134 * i)
                toc_bytes = struct.unpack("256s24s12s12si", caj.read(0x134))
                title = toc_bytes[0].replace(b'\x00', b'').decode("gb18030").encode("utf-8")
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

    def convert(self, dest):
        if self.format == "CAJ":
            self._convert_caj(dest)
        elif self.format == "HN":
            self._convert_hn(dest)

    def _convert_caj(self, dest):
        caj = open(self.filename, "rb")

        # Extract original PDF data (and add header)
        caj.seek(self._PAGE_NUMBER_OFFSET + 4)
        [pdf_start_pointer] = struct.unpack("i", caj.read(4))
        caj.seek(pdf_start_pointer)
        [pdf_start] = struct.unpack("i", caj.read(4))
        pdf_length = fnd(caj, b"<?xml") - pdf_start
        caj.seek(pdf_start)
        pdf_data = b"%PDF-1.3\r\n" + caj.read(pdf_length)
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")

        # Add Catalog (find obj_no of pages)
        inds_addr = [i + 8 for i in fnd_all(pdf, b"/Parent")]
        inds = []
        for addr in inds_addr:
            pdf.seek(addr)
            length = 0
            while True:
                [s] = struct.unpack("s", pdf.read(1))
                if s == b" ":
                    break
                else:
                    length += 1
                    pdf.seek(addr + length)
            pdf.seek(addr)
            [ind] = struct.unpack(str(length) + "s", pdf.read(length))
            inds.append(int(ind))
        pages_obj_no = min(inds)
        catalog = bytes("1 0 obj\r<</Type /Catalog\r/Pages {0} 0 R\r>>\rendobj\r".format(pages_obj_no), "utf-8")
        pdf_data += catalog
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")

        # Add Pages obj and EOF mark
        kids_addr = fnd_all(pdf, b"/Kids")
        inds_addr = []
        for kid in kids_addr:
            ind = kid - 6
            while True:
                pdf.seek(ind)
                [obj_str] = struct.unpack("6s", pdf.read(6))
                if obj_str == b"obj\r<<":
                    break
                else:
                    ind = ind - 1
            ind -= 1
            pdf.seek(ind)
            while True:
                [s] = struct.unpack("s", pdf.read(1))
                if s == b"\r":
                    break
                else:
                    ind -= 1
                    pdf.seek(ind)
            inds_addr.append(ind + 1)
        inds = []
        for addr in inds_addr:
            pdf.seek(addr)
            length = 0
            while True:
                [s] = struct.unpack("s", pdf.read(1))
                if s == b" ":
                    break
                else:
                    length += 1
                    pdf.seek(addr + length)
            pdf.seek(addr)
            [ind] = struct.unpack(str(length) + "s", pdf.read(length))
            inds.append(int(ind))
        inds_str = ["{0} 0 R".format(i) for i in inds]
        kids_str = "[{0}]".format(" ".join(inds_str))
        pages_str = "{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj".format(pages_obj_no, kids_str,
                                                                                            self.page_num)
        pdf_data += bytes(pages_str, "utf-8")
        pdf_data += bytes("\r\n%%EOF\r", "utf-8")
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)

        # Use mutool to repair xref
        call(["mutool", "clean", "pdf.tmp", "pdf_toc.pdf"])

        # Add Outlines
        add_outlines(self.get_toc(), "pdf_toc.pdf", dest)
        call(["rm", "-f", "pdf.tmp"])
        call(["rm", "-f", "pdf_toc.pdf"])

    def _convert_hn(self, dest):
        raise SystemExit("Unsupported file type.")
