from subprocess import check_output, STDOUT, CalledProcessError
from utils import *


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
                ttl_end = toc_bytes[0].find(b"\x00")
                title = toc_bytes[0][0:ttl_end].decode("gb18030").encode("utf-8")
                pg_end = toc_bytes[2].find(b"\x00")
                page = int(toc_bytes[2][0:pg_end])
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
        pdf_end = fnd_all(caj, b"endobj")[-1] + 6
        pdf_length = pdf_end - pdf_start
        caj.seek(pdf_start)
        pdf_data = b"%PDF-1.3\r\n" + caj.read(pdf_length) + b"\r\n"
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")
        
        # deal with disordered PDF data -- to get obj_dict & cntts2pg
        endobj_addr = fnd_all(pdf, b"endobj")
        obj_dict = {}  # object # -> object
        cntts2pg = {}  # contents -> page obj # & parent obj #
        for addr in endobj_addr:
            st_ = fnd_rvrs(pdf, b" 0 obj", addr)
            st_ = max(fnd_rvrs(pdf, b"\r", st_), fnd_rvrs(pdf, b"\n", st_))  # '\r' or '\n' before object
            no = rd_int(pdf, st_)
            if no not in obj_dict:
                obj_len = addr - st_ + 6
                pdf.seek(st_)
                [obj] = struct.unpack(str(obj_len)+"s", pdf.read(obj_len))
                if obj.find(b"/Pages") >= 0:  # discard all pages object(s)
                    continue
                obj_dict[no] = obj
                if obj.find(b"/Contents") >= 0:  # equivalent to that this is a page object
                    con_st = fnd(pdf, b"/Contents", st_) + 10 + (obj.find(b"/Contents [")>=0)  # only one contents # is needed
                    contents = rd_int(pdf, con_st)
                    parent_st = fnd(pdf, b"/Parent ", st_) + 8
                    parent = rd_int(pdf, parent_st)
                    cntts2pg[contents] = {'page': no, 'parent': parent}
        # generate catelog obj # & root pages obj (the only pages obj) #
        ctlg_no = fnd_unuse_no(list(obj_dict.keys()), [])
        root_pgs_no = fnd_unuse_no(list(obj_dict.keys()), [ctlg_no])
        # determine root pages obj's kids
        kids = []
        for no in obj_dict:
            if no in cntts2pg:
                pg = cntts2pg[no]['page']
                kids.append(pg)   # ordered as the order in which contents objs appear in .caj file
                old = bytes("/Parent {0}".format(cntts2pg[no]['parent']), 'utf-8')
                new = bytes("/Parent {0}".format(root_pgs_no), 'utf-8')
                obj_dict[pg] = obj_dict[pg].replace(old, new)  # change all page objects' parent to root pages obj
        # generate catalog obj, root pages obj and final pdf data
        catalog = bytes("{0} 0 obj\r<</Type /Catalog\r/Pages {1} 0 R\r>>\rendobj\r".format(
            ctlg_no, root_pgs_no), "utf-8")
        kids_str = ["{0} 0 R".format(i) for i in kids]
        kids_strs = "[{0}]".format(" ".join(kids_str))
        pages = bytes("{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj\r".format(
            root_pgs_no, kids_strs, self.page_num), 'utf-8')
        objs = list(obj_dict.values())
        pdf_data = b"%PDF-1.3\r\n"
        for obj in objs:
            pdf_data += b'\r' + obj
        pdf_data += b'\r' + pages + b'\r' + catalog
        pdf_data += b"\n%%EOF\r"
        # write pdf data to file
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)

        # Use mutool to repair xref
        try:
            check_output(["mutool", "clean", "pdf.tmp", "pdf_toc.pdf"], stderr=STDOUT)
        except CalledProcessError as e:
            print(e.output.decode("utf-8"))
            raise SystemExit("Command mutool returned non-zero exit status " + str(e.returncode))

        # Add Outlines
        add_outlines(self.get_toc(), "pdf_toc.pdf", dest)
        os.remove("pdf.tmp")
        os.remove("pdf_toc.pdf")

    def _convert_hn(self, dest):
        raise SystemExit("Unsupported file type.")
