import os
import struct
from shutil import copy
from subprocess import check_output, STDOUT, CalledProcessError
from utils import fnd, fnd_all, add_outlines, fnd_rvrs, fnd_unuse_no

KDH_PASSPHRASE = b"FZHMEI"


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
            elif fmt == "%PDF":
                self.format = "PDF"
            elif fmt == "KDH ":
                self.format = "KDH"
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
        elif self.format == "PDF":
            self._convert_pdf(dest)
        elif self.format == "KDH":
            self._convert_kdh(dest)

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

        # deal with disordered PDF data
        endobj_addr = fnd_all(pdf, b"endobj")
        pdf_data = b"%PDF-1.3\r\n"
        obj_no = []
        for addr in endobj_addr:
            startobj = fnd_rvrs(pdf, b" 0 obj", addr)
            startobj1 = fnd_rvrs(pdf, b"\r", startobj)
            startobj2 = fnd_rvrs(pdf, b"\n", startobj)
            startobj = max(startobj1, startobj2)
            length = fnd(pdf, b" ", startobj) - startobj
            pdf.seek(startobj)
            [no] = struct.unpack(str(length) + "s", pdf.read(length))
            if int(no) not in obj_no:
                obj_no.append(int(no))
                obj_len = addr - startobj + 6
                pdf.seek(startobj)
                [obj] = struct.unpack(str(obj_len) + "s", pdf.read(obj_len))
                pdf_data += (b"\r" + obj)
        pdf_data += b"\r\n"
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")

        # Add Catalog (find obj_no of pages)
        inds_addr = [i + 8 for i in fnd_all(pdf, b"/Parent")]
        inds = []
        for addr in inds_addr:
            length = fnd(pdf, b" ", addr) - addr
            pdf.seek(addr)
            [ind] = struct.unpack(str(length) + "s", pdf.read(length))
            inds.append(int(ind))
        # get pages_obj_no list containing distinct elements
        # & find missing pages object(s) -- top pages object(s) in pages_obj_no
        pages_obj_no = []
        top_pages_obj_no = []
        for ind in inds:
            if (ind not in pages_obj_no) and (ind not in top_pages_obj_no):
                if fnd(pdf, bytes("\r{0} 0 obj".format(ind), "utf-8")) == -1:
                    top_pages_obj_no.append(ind)
                else:
                    pages_obj_no.append(ind)
        single_pages_obj_missed = len(top_pages_obj_no) == 1
        multi_pages_obj_missed = len(top_pages_obj_no) > 1
        # generate catalog object
        catalog_obj_no = fnd_unuse_no(obj_no, top_pages_obj_no)
        obj_no.append(catalog_obj_no)
        root_pages_obj_no = None
        if multi_pages_obj_missed:
            root_pages_obj_no = fnd_unuse_no(obj_no, top_pages_obj_no)
        elif single_pages_obj_missed:
            root_pages_obj_no = top_pages_obj_no[0]
            top_pages_obj_no = pages_obj_no
        else:  # root pages object exists, then find the root pages object #
            found = False
            for pon in pages_obj_no:
                tmp_addr = fnd(pdf, bytes("\r{0} 0 obj".format(pon), 'utf-8'))
                while True:
                    pdf.seek(tmp_addr)
                    [_str] = struct.unpack("6s", pdf.read(6))
                    if _str == b"Parent":
                        break
                    elif _str == b"endobj":
                        root_pages_obj_no = pon
                        found = True
                        break
                    tmp_addr = tmp_addr + 1
                if found:
                    break
        catalog = bytes("{0} 0 obj\r<</Type /Catalog\r/Pages {1} 0 R\r>>\rendobj\r".format(
            catalog_obj_no, root_pages_obj_no), "utf-8")
        pdf_data += catalog
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")

        # Add Pages obj and EOF mark
        # if root pages object exist, pass
        # deal with single missing pages object
        if single_pages_obj_missed or multi_pages_obj_missed:
            inds_str = ["{0} 0 R".format(i) for i in top_pages_obj_no]
            kids_str = "[{0}]".format(" ".join(inds_str))
            pages_str = "{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj\r".format(
                root_pages_obj_no, kids_str, self.page_num)
            pdf_data += bytes(pages_str, "utf-8")
            with open("pdf.tmp", 'wb') as f:
                f.write(pdf_data)
            pdf = open("pdf.tmp", "rb")
        # deal with multiple missing pages objects
        if multi_pages_obj_missed:
            kids_dict = {i: [] for i in top_pages_obj_no}
            count_dict = {i: 0 for i in top_pages_obj_no}
            for tpon in top_pages_obj_no:
                kids_addr = fnd_all(pdf, bytes("/Parent {0} 0 R".format(tpon), "utf-8"))
                for kid in kids_addr:
                    ind = fnd_rvrs(pdf, b"obj", kid) - 4
                    addr = fnd_rvrs(pdf, b"\r", ind)
                    length = fnd(pdf, b" ", addr) - addr
                    pdf.seek(addr)
                    [ind] = struct.unpack(str(length) + "s", pdf.read(length))
                    kids_dict[tpon].append(int(ind))
                    type_addr = fnd(pdf, b"/Type", addr) + 5
                    tmp_addr = fnd(pdf, b"/", type_addr) + 1
                    pdf.seek(tmp_addr)
                    [_type] = struct.unpack("5s", pdf.read(5))
                    if _type == b"Pages":
                        cnt_addr = fnd(pdf, b"/Count ", addr) + 7
                        pdf.seek(cnt_addr)
                        [_str] = struct.unpack("1s", pdf.read(1))
                        cnt_len = 0
                        while _str not in [b" ", b"\r", b"/"]:
                            cnt_len += 1
                            pdf.seek(cnt_addr + cnt_len)
                            [_str] = struct.unpack("1s", pdf.read(1))
                        pdf.seek(cnt_addr)
                        [cnt] = struct.unpack(str(cnt_len) + "s", pdf.read(cnt_len))
                        count_dict[tpon] += int(cnt)
                    else:  # _type == b"Page"
                        count_dict[tpon] += 1
                kids_no_str = ["{0} 0 R".format(i) for i in kids_dict[tpon]]
                kids_str = "[{0}]".format(" ".join(kids_no_str))
                pages_str = "{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj\r".format(
                    tpon, kids_str, count_dict[tpon])
                pdf_data += bytes(pages_str, "utf-8")
        pdf_data += bytes("\n%%EOF\r", "utf-8")
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
        pdf.close()
        os.remove("pdf.tmp")
        os.remove("pdf_toc.pdf")

    def _convert_hn(self, dest):
        raise SystemExit("Unsupported file type.")

    def _convert_pdf(self, dest):
        copy(self.filename, dest)

    def _convert_kdh(self, dest):
        #  Read KDH file.
        fp = open(self.filename, "rb")
        origin = fp.read()
        fp.close()

        #  Decrypt.
        origin = origin[254:]
        output = []
        keycursor = 0
        for origin_byte in origin:
            output.append(origin_byte ^ KDH_PASSPHRASE[keycursor])
            keycursor += 1
            if keycursor >= len(KDH_PASSPHRASE):
                keycursor = 0
        output = bytes(output)

        #  Remove useless tail data.
        eofpos = output.rfind(b"%%EOF")
        if eofpos < 0:
            raise Exception("%%EOF mark can't be found.")
        output = output[:eofpos + 5]

        #  Write output file.
        fp = open(dest + ".tmp", "wb")
        fp.write(output)
        fp.close()

        # Use mutool to repair xref
        try:
            check_output(["mutool", "clean", dest + ".tmp", dest], stderr=STDOUT)
        except CalledProcessError as e:
            print(e.output.decode("utf-8"))
            raise SystemExit("Command mutool returned non-zero exit status " + str(e.returncode))

        os.remove(dest + ".tmp")
