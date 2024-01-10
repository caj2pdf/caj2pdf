import os
import struct
from shutil import copy
from subprocess import check_output, STDOUT, CalledProcessError
from utils import fnd, fnd_all, add_outlines, fnd_rvrs, fnd_unuse_no, find_redundant_images

try:
    from PyPDF2 import errors
except ImportError:
    from PyPDF2 import utils as errors

KDH_PASSPHRASE = b"FZHMEI"

printables = ''.join([(len(repr(chr(x)))==3) and (x != 47) and (x < 128) and chr(x) or '.' for x in range(256)])

image_type = {
    0 : "JBIG",
    1 : "JPEG",
    2 : "JPEG", # up-side-down
    3 : "JBIG2"
    }

class CAJParser(object):
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(filename, "rb") as caj:
                caj_read4 = caj.read(4)
                if (caj_read4[0:1] == b'\xc8'):
                    self.format = "C8"
                    self._PAGE_NUMBER_OFFSET = 0x08
                    self._TOC_NUMBER_OFFSET = 0 # No TOC
                    self._TOC_END_OFFSET = 0x50
                    self._PAGEDATA_OFFSET = self._TOC_END_OFFSET + 20 * self.page_num
                    return
                if (caj_read4[0:2] == b'HN'):
                    if (caj.read(2) == b'\xc8\x00'): # Most of them are: 90 01, handled later
                        self.format = "HN"
                        self._PAGE_NUMBER_OFFSET = 0x90
                        self._TOC_NUMBER_OFFSET = 0
                        self._TOC_END_OFFSET = 0xD8
                        self._PAGEDATA_OFFSET = self._TOC_END_OFFSET + 20 * self.page_num
                        return
                fmt = struct.unpack("4s", caj_read4)[0].replace(b'\x00', b'').decode("gb18030")
            if fmt == "CAJ":
                self.format = "CAJ"
                self._PAGE_NUMBER_OFFSET = 0x10
                self._TOC_NUMBER_OFFSET = 0x110
            elif fmt == "HN":
                self.format = "HN"
                self._PAGE_NUMBER_OFFSET = 0x90
                self._TOC_NUMBER_OFFSET = 0x158

                # TOC = [toc_num] followed by [toc_entry * toc_num]
                # followed by [Page Info struct (20-byte) * page_num], followed by Page Data
                self._TOC_END_OFFSET = self._TOC_NUMBER_OFFSET + 4 + 0x134 * self.toc_num
                self._PAGEDATA_OFFSET = self._TOC_END_OFFSET + 20 * self.page_num
            elif fmt == "%PDF":
                self.format = "PDF"
            elif fmt == "KDH ":
                self.format = "KDH"
            elif fmt == "TEB":
                self.format = "TEB"
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
        if (self._TOC_NUMBER_OFFSET == 0):
            return 0
        with open(self.filename, "rb") as caj:
            caj.seek(self._TOC_NUMBER_OFFSET)
            [toc_num] = struct.unpack("i", caj.read(4))
            return toc_num

    def get_toc(self, verbose=False):
        toc = []
        if (self._TOC_NUMBER_OFFSET == 0):
            return toc
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
                if ( verbose ):
                    print("   " * (level -1), title.decode("utf-8"))
                toc.append(toc_entry)
            if ( verbose ):
                print("TOC END: 0x%04X" % (self._TOC_NUMBER_OFFSET + 4 + 0x134 * self.toc_num))
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
        elif self.format == "C8":
            self._convert_hn(dest)
        elif self.format == "PDF":
            self._convert_pdf(dest)
        elif self.format == "KDH":
            self._convert_kdh(dest)

    def parse(self):
        if self.format == "CAJ":
            pass
        elif self.format == "HN":
            self._parse_hn()
        elif self.format == "C8":
            self._parse_hn()
        elif self.format == "PDF":
            pass
        elif self.format == "KDH":
            pass

    def text_extract(self):
        if self.format == "CAJ":
            pass
        if self.format == "HN":
            self._text_extract_hn()
        elif self.format == "C8":
            self._text_extract_hn()
        elif self.format == "PDF":
            pass
        elif self.format == "KDH":
            pass

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
        pdf.close()
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
            pdf.close()
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
        pdf.close()
        with open("pdf.tmp", 'wb') as f:
            f.write(pdf_data)

        # Use mutool to repair xref
        try:
            check_output(["mutool", "clean", "pdf.tmp", "pdf_toc.pdf"], stderr=STDOUT)
        except CalledProcessError as e:
            print(e.output.decode("utf-8"))
            print("Command mutool returned non-zero exit status " + str(e.returncode))
            print("Try merge mode...")
            os.remove("pdf_toc.pdf")
            try:
                 check_output(["mutool", "merge", "-opdf_toc.pdf", "pdf.tmp"], stderr=STDOUT)
            except CalledProcessError as e:
                    print(e.output.decode("utf-8"))
                    SystemExit("Merge mode also failed.")
            

        # Add Outlines
        try:
            add_outlines(self.get_toc(), "pdf_toc.pdf", dest)
        except errors.PdfReadError as e:
            print("errors.PdfReadError:", str(e))
            copy("pdf_toc.pdf", dest)
            pass
        os.remove("pdf.tmp")
        os.remove("pdf_toc.pdf")

    def _convert_hn(self, dest):
        caj = open(self.filename, "rb")
        image_list = []

        from pdfwutils import Colorspace, ImageFormat, convert_ImageList
        import zlib

        for i in range(self.page_num):
            caj.seek(self._TOC_END_OFFSET + i * 20)
            [page_data_offset, size_of_text_section, images_per_page, page_no, unk2, next_page_data_offset] = struct.unpack("iihhii", caj.read(20))
            caj.seek(page_data_offset)
            text_header_read32 = caj.read(32)
            if ((text_header_read32[8:20] == b'COMPRESSTEXT') or (text_header_read32[0:12] == b'COMPRESSTEXT')):
                coff = 8
                if (text_header_read32[0:12] == b'COMPRESSTEXT'):
                    coff = 0
                [expanded_text_size] = struct.unpack("i", text_header_read32[12+coff:16+coff])
                import zlib
                caj.seek(page_data_offset + 16 + coff)
                data = caj.read(size_of_text_section - 16 - coff)
                output = zlib.decompress(data, bufsize=expanded_text_size)
                if (len(output) != expanded_text_size):
                    raise SystemExit("Unexpected:", len(output), expanded_text_size)
            else:
                caj.seek(page_data_offset)
                output = caj.read(size_of_text_section)
            from HNParsePage import HNParsePage
            page_style = (next_page_data_offset > page_data_offset)
            page_data = HNParsePage(output, page_style)

            current_offset = page_data_offset + size_of_text_section
            (found, images_per_page) = find_redundant_images(caj, current_offset, images_per_page)
            if (found):
                print("Page %d, skipping %d redundant images" % (i+1, images_per_page * ( images_per_page - 1)))

            if (images_per_page > 1):
                if (len(page_data.figures) == images_per_page):
                    if (page_data.figures[0][0] == 0) and (page_data.figures[0][1] == 0):
                        image_list.append(None)
                        image_list.append(page_data.figures)
                    else:
                        print("Page %d, Image Count %d, first image not at origin, expanding to %d pages"
                              % (i+1, len(page_data.figures), images_per_page))
                else:
                    print("Page %d, Image Count %d != %d" % (i+1, len(page_data.figures), images_per_page))
                    if (len(page_data.figures) > images_per_page):
                        print("\tTruncating Page %d," % (i+1), page_data.figures)
                        image_list.append(None)
                        image_list.append(page_data.figures[0:images_per_page])
                    else:
                        print("Page %d expanding to %d separate image pages" % (i+1, images_per_page))
            elif (images_per_page == 1):
                if ((len(page_data.figures) == 0) or
                    ((len(page_data.figures) > 0) and
                    (not ((page_data.figures[0][0] == 0) and (page_data.figures[0][1] == 0))))):
                    print("Page %d possibly text-only + single figure(%d)" % (i+1, len(page_data.figures)))
            else:
                # don't care about images_per_page == 0
                pass
            for j in range(images_per_page):
                caj.seek(current_offset)
                read32 = caj.read(32)
                [image_type_enum, offset_to_image_data, size_of_image_data] = struct.unpack("iii", read32[0:12])
                if (offset_to_image_data != current_offset + 12):
                    raise SystemExit("unusual image offset")
                caj.seek(offset_to_image_data)
                image_data = caj.read(size_of_image_data)
                current_offset = offset_to_image_data + size_of_image_data
                if (image_type[image_type_enum] == "JBIG"):
                    from jbigdec import CImage
                    cimage = CImage(image_data)
                    out = cimage.DecodeJbig()
                    # PBM is only padded to 8 rather than 32.
                    # If the padding is larger, write padded file.
                    width = cimage.width
                    if (cimage.bytes_per_line > ((cimage.width +7) >> 3)):
                        width = cimage.bytes_per_line << 3
                    image_item = (
                        Colorspace.P,
                        (300, 300),
                        ImageFormat.PBM,
                        zlib.compress(out),
                        width,
                        cimage.height,
                        [0xffffff, 0],
                        False,
                        1,
                        0
                    )
                elif (image_type[image_type_enum] == "JBIG2"):
                    from jbig2dec import CImage
                    cimage = CImage(image_data)
                    out = cimage.DecodeJbig2()
                    # PBM is only padded to 8 rather than 32.
                    # If the padding is larger, write padded file.
                    width = cimage.width
                    if (cimage.bytes_per_line > ((cimage.width +7) >> 3)):
                        width = cimage.bytes_per_line << 3
                    image_item = (
                        Colorspace.P,
                        (300, 300),
                        ImageFormat.PBM,
                        zlib.compress(out),
                        width,
                        cimage.height,
                        [0xffffff, 0],
                        False,
                        1,
                        0
                    )
                elif (image_type[image_type_enum] == "JPEG"):
                    colorspace = Colorspace.RGB
                    component = 3
                    # stock libjpeg location
                    (SOFn, frame_length, bits_per_pixel, height, width, component) = struct.unpack(">HHBHHB", image_data[158:168])
                    if (SOFn != 0xFFC0):
                        # "Intel(R) JPEG Library" location
                        (SOFn, frame_length, bits_per_pixel, height, width, component) = struct.unpack(">HHBHHB", image_data[0x272:0x27c])
                        if (SOFn != 0xFFC0):
                            # neither works, try brute-force
                            import imagesize
                            from PIL import Image as pilimage
                            with open(".tmp.jpg", "wb") as f:
                                f.write(image_data)
                                (width, height) = imagesize.get(".tmp.jpg")
                                pim = pilimage.open(".tmp.jpg")
                                if (pim.mode == 'L'):
                                    component = 1
                            os.remove(".tmp.jpg")
                    if (image_type_enum == 1):
                        # non-inverted JPEG Images
                        height = -height
                    if (component == 1):
                        colorspace = Colorspace.L
                    image_item = (
                        colorspace,
                        (300, 300),
                        ImageFormat.JPEG,
                        image_data,
                        width,
                        height,
                        [],
                        False,
                        8,
                        0
                    )
                else:
                    raise SystemExit("Unknown Image Type %d" % (image_type_enum))
                image_list.append(image_item)
        if (len(image_list) == 0):
            raise SystemExit("File is pure-text HN; cannot convert to pdf")
        pdf_data = convert_ImageList(image_list)
        with open('pdf_toc.pdf', 'wb') as f:
            f.write(pdf_data)
        # Add Outlines
        add_outlines(self.get_toc(), "pdf_toc.pdf", dest)
        os.remove("pdf_toc.pdf")

    def _text_extract_hn(self):
        if (self._TOC_NUMBER_OFFSET > 0):
            self.get_toc(verbose=True)
        caj = open(self.filename, "rb")

        for i in range(self.page_num):
            caj.seek(self._TOC_END_OFFSET + i * 20)
            [page_data_offset, size_of_text_section, images_per_page, page_no, unk2, next_page_data_offset] = struct.unpack("iihhii", caj.read(20))
            caj.seek(page_data_offset)
            text_header_read32 = caj.read(32)
            if ((text_header_read32[8:20] == b'COMPRESSTEXT') or (text_header_read32[0:12] == b'COMPRESSTEXT')):
                coff = 8
                if (text_header_read32[0:12] == b'COMPRESSTEXT'):
                    coff = 0
                [expanded_text_size] = struct.unpack("i", text_header_read32[12+coff:16+coff])
                import zlib
                caj.seek(page_data_offset + 16 + coff)
                data = caj.read(size_of_text_section - 16 - coff)
                output = zlib.decompress(data, bufsize=expanded_text_size)
                if (len(output) != expanded_text_size):
                    raise SystemExit("Unexpected:", len(output), expanded_text_size)
            else:
                caj.seek(page_data_offset)
                output = caj.read(size_of_text_section)
            from HNParsePage import HNParsePage
            page_style = (next_page_data_offset > page_data_offset)
            page_data = HNParsePage(output, page_style)
            print("Text on Page %d:" % (i+1))
            print(page_data.texts)
            #print("Figures:\n", page_data.figures)

    def _parse_hn(self):
        if (self._TOC_NUMBER_OFFSET > 0):
            self.get_toc(verbose=True)
        caj = open(self.filename, "rb")

        for i in range(self.page_num):
            caj.seek(self._TOC_END_OFFSET + i * 20)
            print("Reading Page Info struct #%d at offset 0x%04X" % (i+1, self._TOC_END_OFFSET + i * 20))
            [page_data_offset, size_of_text_section, images_per_page, page_no, unk2, next_page_data_offset] = struct.unpack("iihhii", caj.read(20))
            print("unknown page struct members = (%d %d)" % (unk2, next_page_data_offset))
            # All 71: 1,0,0
            print("Page Number %d Data offset = 0x%04X" % (page_no, page_data_offset))
            caj.seek(page_data_offset)
            text_header_read32 = caj.read(32)
            print("Page Text Header dump:\n", self.dump(text_header_read32), sep="")
            # The first 8 bytes are always: 03 80 XX 16 03 80 XX XX,
            # the last one 20 or 21, but the first two can be any.
            # 48/71 has: 03 80 E0 16 03 80 F7 20, the rest uniq
            if ((text_header_read32[8:20] == b'COMPRESSTEXT') or (text_header_read32[0:12] == b'COMPRESSTEXT')):
                coff = 8
                if (text_header_read32[0:12] == b'COMPRESSTEXT'):
                    coff = 0
                # expanded_text_size seems to be always about 2-3 times size_of_text_section, so this is a guess.
                [expanded_text_size] = struct.unpack("i", text_header_read32[12+coff:16+coff])
                import zlib
                caj.seek(page_data_offset + 16 + coff)
                data = caj.read(size_of_text_section - 16 - coff)
                output = zlib.decompress(data, bufsize=expanded_text_size)
                if (len(output) != expanded_text_size):
                    print("Unexpected:", len(output), expanded_text_size)
                print("Page Text Header COMPRESSTEXT:\n", self.dump(output, GB=True), sep="")
                for x in range(len(output) >> 4):
                    try:
                        print(bytes([output[(x << 4) + 7],output[(x << 4) + 6]]).decode("gbk"), end="")
                    except UnicodeDecodeError:
                        print(self.dump(output[x << 4:(x+1) << 4]))
                print()
            else:
                caj.seek(page_data_offset)
                output = caj.read(size_of_text_section)
                print("Page Text Header non-COMPRESSTEXT:\n", self.dump(output, GB=True), sep="")
            from HNParsePage import HNParsePage
            page_style = (next_page_data_offset > page_data_offset)
            page_data = HNParsePage(output, page_style)
            print("Text:\n", page_data.texts)
            print("Figures:\n", page_data.figures)
            current_offset = page_data_offset + size_of_text_section
            for j in range(images_per_page):
                caj.seek(current_offset)
                read32 = caj.read(32)
                [image_type_enum, offset_to_image_data, size_of_image_data] = struct.unpack("iii", read32[0:12])
                if (image_type[image_type_enum] != "JPEG"):
                    read32 += caj.read(64)
                print("size of image data = %d (%s)" % (size_of_image_data, image_type[image_type_enum]))
                if (offset_to_image_data != current_offset + 12):
                    raise SystemExit("unusual image offset")
                print("Page Image Header dump:\n", self.dump(read32), sep="")
                print("Expected End of Page #%d: 0x%08X" % (i+1, current_offset + size_of_image_data + 12))
                caj.seek(offset_to_image_data)
                image_data = caj.read(size_of_image_data)
                current_offset = offset_to_image_data + size_of_image_data
                image_name = "image_dump_%04d" % (i+1)
                if (j > 0):
                    image_name = "image_dump_%04d_%04d" % (i+1, j)
                with open(image_name + ".dat", "wb") as f:
                    f.write(image_data)
                if (image_type[image_type_enum] == "JBIG"):
                    try:
                        from jbigdec import SaveJbigAsBmp
                        SaveJbigAsBmp(image_data, size_of_image_data, (image_name + ".bmp").encode('ascii'))
                    except ImportError:
                        pass
                elif (image_type[image_type_enum] == "JBIG2"):
                    try:
                        from jbigdec import SaveJbig2AsBmp
                        SaveJbig2AsBmp(image_data, size_of_image_data, (image_name + ".bmp").encode('ascii'))
                    except ImportError:
                        pass
                elif (image_type[image_type_enum] == "JPEG"):
                    with open(image_name + ".jpg", "wb") as f:
                        f.write(image_data)
        print("end 0x%08x" % self._PAGEDATA_OFFSET)

    def dump(self, src, GB=False):
        N=0
        result=[]
        while src:
            s,src = src[:16],src[16:]
            hexa = ' '.join(["%02X"% x for x in s])
            gb = ""
            if (GB):
                gb += "    "
                for x in range(len(s) >> 1):
                    try:
                        if (s[(x << 1) +1] < 128 and s[(x << 1) + 0] < 128):
                            gb += ".."
                        else:
                            gb += bytes([s[(x << 1) + 1],s[(x << 1) + 0]]).decode("gbk")
                    except UnicodeDecodeError:
                        gb += ".."
            s = ''.join(printables[x] for x in s)
            result += "%04X   %-*s   %s%s\n" % (N, 16*3, hexa, s, gb)
            N+=16
        return ''.join(result)


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
