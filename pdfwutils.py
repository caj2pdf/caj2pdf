# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Johannes 'josch' Schauer <j.schauer at email.de>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

# Portions Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#     - img2pdf 0.3.4 renamed and adapted for usage by caj2pdf
#
# The main changes are:
#
# - removal of large GUI routine and dependencies on PIL
#   (and zlib.deflate 1-bit input, rather than ccitt-g4 compress them)
#
# - different default dpi, inverting images
#
# - allow feeding input images directly from memory, instead of reading from disk
#
# - remove dependency on pdfrw

import sys
import os
import zlib
import argparse
#from PIL import Image

# TiffImagePlugin.DEBUG = True
from datetime import datetime
#from jp2 import parsejp2
from enum import Enum
from io import BytesIO
import logging
import struct
import platform

PY3 = sys.version_info[0] >= 3

__version__ = "0.3.4"
default_dpi = 300.0
papersizes = {
    "letter": "8.5inx11in",
    "a0": "841mmx1189mm",
    "a1": "594mmx841mm",
    "a2": "420mmx594mm",
    "a3": "297mmx420mm",
    "a4": "210mmx297mm",
    "a5": "148mmx210mm",
    "a6": "105mmx148mm",
    "legal": "8.5inx14in",
    "tabloid": "11inx17in",
}
papernames = {
    "letter": "Letter",
    "a0": "A0",
    "a1": "A1",
    "a2": "A2",
    "a3": "A3",
    "a4": "A4",
    "a5": "A5",
    "a6": "A6",
    "legal": "Legal",
    "tabloid": "Tabloid",
}


FitMode = Enum("FitMode", "into fill exact shrink enlarge")

PageOrientation = Enum("PageOrientation", "portrait landscape")

Colorspace = Enum("Colorspace", "RGB L 1 CMYK CMYK;I RGBA P other")

ImageFormat = Enum("ImageFormat", "JPEG JPEG2000 CCITTGroup4 PNG TIFF PBM other")

PageMode = Enum("PageMode", "none outlines thumbs")

PageLayout = Enum("PageLayout", "single onecolumn twocolumnright twocolumnleft")

Magnification = Enum("Magnification", "fit fith fitbh")

ImgSize = Enum("ImgSize", "abs perc dpi")

Unit = Enum("Unit", "pt cm mm inch")

ImgUnit = Enum("ImgUnit", "pt cm mm inch perc dpi")

TIFFBitRevTable = [
    0x00,
    0x80,
    0x40,
    0xC0,
    0x20,
    0xA0,
    0x60,
    0xE0,
    0x10,
    0x90,
    0x50,
    0xD0,
    0x30,
    0xB0,
    0x70,
    0xF0,
    0x08,
    0x88,
    0x48,
    0xC8,
    0x28,
    0xA8,
    0x68,
    0xE8,
    0x18,
    0x98,
    0x58,
    0xD8,
    0x38,
    0xB8,
    0x78,
    0xF8,
    0x04,
    0x84,
    0x44,
    0xC4,
    0x24,
    0xA4,
    0x64,
    0xE4,
    0x14,
    0x94,
    0x54,
    0xD4,
    0x34,
    0xB4,
    0x74,
    0xF4,
    0x0C,
    0x8C,
    0x4C,
    0xCC,
    0x2C,
    0xAC,
    0x6C,
    0xEC,
    0x1C,
    0x9C,
    0x5C,
    0xDC,
    0x3C,
    0xBC,
    0x7C,
    0xFC,
    0x02,
    0x82,
    0x42,
    0xC2,
    0x22,
    0xA2,
    0x62,
    0xE2,
    0x12,
    0x92,
    0x52,
    0xD2,
    0x32,
    0xB2,
    0x72,
    0xF2,
    0x0A,
    0x8A,
    0x4A,
    0xCA,
    0x2A,
    0xAA,
    0x6A,
    0xEA,
    0x1A,
    0x9A,
    0x5A,
    0xDA,
    0x3A,
    0xBA,
    0x7A,
    0xFA,
    0x06,
    0x86,
    0x46,
    0xC6,
    0x26,
    0xA6,
    0x66,
    0xE6,
    0x16,
    0x96,
    0x56,
    0xD6,
    0x36,
    0xB6,
    0x76,
    0xF6,
    0x0E,
    0x8E,
    0x4E,
    0xCE,
    0x2E,
    0xAE,
    0x6E,
    0xEE,
    0x1E,
    0x9E,
    0x5E,
    0xDE,
    0x3E,
    0xBE,
    0x7E,
    0xFE,
    0x01,
    0x81,
    0x41,
    0xC1,
    0x21,
    0xA1,
    0x61,
    0xE1,
    0x11,
    0x91,
    0x51,
    0xD1,
    0x31,
    0xB1,
    0x71,
    0xF1,
    0x09,
    0x89,
    0x49,
    0xC9,
    0x29,
    0xA9,
    0x69,
    0xE9,
    0x19,
    0x99,
    0x59,
    0xD9,
    0x39,
    0xB9,
    0x79,
    0xF9,
    0x05,
    0x85,
    0x45,
    0xC5,
    0x25,
    0xA5,
    0x65,
    0xE5,
    0x15,
    0x95,
    0x55,
    0xD5,
    0x35,
    0xB5,
    0x75,
    0xF5,
    0x0D,
    0x8D,
    0x4D,
    0xCD,
    0x2D,
    0xAD,
    0x6D,
    0xED,
    0x1D,
    0x9D,
    0x5D,
    0xDD,
    0x3D,
    0xBD,
    0x7D,
    0xFD,
    0x03,
    0x83,
    0x43,
    0xC3,
    0x23,
    0xA3,
    0x63,
    0xE3,
    0x13,
    0x93,
    0x53,
    0xD3,
    0x33,
    0xB3,
    0x73,
    0xF3,
    0x0B,
    0x8B,
    0x4B,
    0xCB,
    0x2B,
    0xAB,
    0x6B,
    0xEB,
    0x1B,
    0x9B,
    0x5B,
    0xDB,
    0x3B,
    0xBB,
    0x7B,
    0xFB,
    0x07,
    0x87,
    0x47,
    0xC7,
    0x27,
    0xA7,
    0x67,
    0xE7,
    0x17,
    0x97,
    0x57,
    0xD7,
    0x37,
    0xB7,
    0x77,
    0xF7,
    0x0F,
    0x8F,
    0x4F,
    0xCF,
    0x2F,
    0xAF,
    0x6F,
    0xEF,
    0x1F,
    0x9F,
    0x5F,
    0xDF,
    0x3F,
    0xBF,
    0x7F,
    0xFF,
]


class NegativeDimensionError(Exception):
    pass


class UnsupportedColorspaceError(Exception):
    pass


class ImageOpenError(Exception):
    pass


class JpegColorspaceError(Exception):
    pass


class PdfTooLargeError(Exception):
    pass


class AlphaChannelError(Exception):
    pass


class ExifOrientationError(Exception):
    pass


# without pdfrw this function is a no-op
def my_convert_load(string):
    return string


def parse(cont, indent=1):
    if type(cont) is dict:
        return (
            b"<<\n"
            + b"\n".join(
                [
                    4 * indent * b" " + k + b" " + parse(v, indent + 1)
                    for k, v in sorted(cont.items())
                ]
            )
            + b"\n"
            + 4 * (indent - 1) * b" "
            + b">>"
        )
    elif type(cont) is int:
        return str(cont).encode()
    elif type(cont) is float:
        if int(cont) == cont:
            return parse(int(cont))
        else:
            return ("%0.4f" % cont).rstrip("0").encode()
    elif isinstance(cont, MyPdfDict):
        # if cont got an identifier, then addobj() has been called with it
        # and a link to it will be added, otherwise add it inline
        if hasattr(cont, "identifier"):
            return ("%d 0 R" % cont.identifier).encode()
        else:
            return parse(cont.content, indent)
    elif type(cont) is str or isinstance(cont, bytes):
        if type(cont) is str and type(cont) is not bytes:
            raise TypeError(
                "parse must be passed a bytes object in py3. Got: %s" % cont
            )
        return cont
    elif isinstance(cont, list):
        return b"[ " + b" ".join([parse(c, indent) for c in cont]) + b" ]"
    else:
        raise TypeError("cannot handle type %s with content %s" % (type(cont), cont))


class MyPdfDict(object):
    def __init__(self, *args, **kw):
        self.content = dict()
        if args:
            if len(args) == 1:
                args = args[0]
            self.content.update(args)
        self.stream = None
        for key, value in kw.items():
            if key == "stream":
                self.stream = value
                self.content[MyPdfName.Length] = len(value)
            elif key == "indirect":
                pass
            else:
                self.content[getattr(MyPdfName, key)] = value

    def tostring(self):
        if self.stream is not None:
            return (
                ("%d 0 obj\n" % self.identifier).encode()
                + parse(self.content)
                + b"\nstream\n"
                + self.stream
                + b"\nendstream\nendobj\n"
            )
        else:
            return (
                ("%d 0 obj\n" % self.identifier).encode()
                + parse(self.content)
                + b"\nendobj\n"
            )

    def __setitem__(self, key, value):
        self.content[key] = value

    def __getitem__(self, key):
        return self.content[key]

    def __contains__(self, key):
        return key in self.content


class MyPdfName:
    def __getattr__(self, name):
        return b"/" + name.encode("ascii")


MyPdfName = MyPdfName()


class MyPdfObject(bytes):
    def __new__(cls, string):
        return bytes.__new__(cls, string.encode("ascii"))


class MyPdfArray(list):
    pass


class MyPdfWriter:
    def __init__(self, version="1.3"):
        self.objects = []
        # create an incomplete pages object so that a /Parent entry can be
        # added to each page
        self.pages = MyPdfDict(Type=MyPdfName.Pages, Kids=[], Count=0)
        self.catalog = MyPdfDict(Pages=self.pages, Type=MyPdfName.Catalog)
        self.version = version  # default pdf version 1.3
        self.pagearray = []

    def addobj(self, obj):
        newid = len(self.objects) + 1
        obj.identifier = newid
        self.objects.append(obj)

    def tostream(self, info, stream):
        xreftable = list()

        # justification of the random binary garbage in the header from
        # adobe:
        #
        #  > Note: If a PDF file contains binary data, as most do (see Section
        #  > 3.1, “Lexical Conventions”), it is recommended that the header
        #  > line be immediately followed by a comment line containing at
        #  > least four binary characters—that is, characters whose codes are
        #  > 128 or greater. This ensures proper behavior of file transfer
        #  > applications that inspect data near the beginning of a file to
        #  > determine whether to treat the file’s contents as text or as
        #  > binary.
        #
        # the choice of binary characters is arbitrary but those four seem to
        # be used elsewhere.
        pdfheader = ("%%PDF-%s\n" % self.version).encode("ascii")
        pdfheader += b"%\xe2\xe3\xcf\xd3\n"
        stream.write(pdfheader)

        # From section 3.4.3 of the PDF Reference (version 1.7):
        #
        #  > Each entry is exactly 20 bytes long, including the end-of-line
        #  > marker.
        #  >
        #  > [...]
        #  >
        #  > The format of an in-use entry is
        #  > nnnnnnnnnn ggggg n eol
        #  > where
        #  > nnnnnnnnnn is a 10-digit byte offset
        #  > ggggg is a 5-digit generation number
        #  > n is a literal keyword identifying this as an in-use entry
        #  > eol is a 2-character end-of-line sequence
        #  >
        #  > [...]
        #  >
        #  > If the file’s end-of-line marker is a single character (either a
        #  > carriage return or a line feed), it is preceded by a single space;
        #
        # Since we chose to use a single character eol marker, we precede it by
        # a space
        pos = len(pdfheader)
        xreftable.append(b"0000000000 65535 f \n")
        for o in self.objects:
            xreftable.append(("%010d 00000 n \n" % pos).encode())
            content = o.tostring()
            stream.write(content)
            pos += len(content)

        xrefoffset = pos
        stream.write(b"xref\n")
        stream.write(("0 %d\n" % len(xreftable)).encode())
        for x in xreftable:
            stream.write(x)
        stream.write(b"trailer\n")
        stream.write(
            parse({b"/Size": len(xreftable), b"/Info": info, b"/Root": self.catalog})
            + b"\n"
        )
        stream.write(b"startxref\n")
        stream.write(("%d\n" % xrefoffset).encode())
        stream.write(b"%%EOF\n")
        return

    def addpage(self, page):
        page[b"/Parent"] = self.pages
        self.pagearray.append(page)
        self.pages.content[b"/Kids"].append(page)
        self.pages.content[b"/Count"] += 1
        self.addobj(page)


if PY3:

    class MyPdfString:
        @classmethod
        def encode(cls, string, hextype=False):
            if hextype:
                return (
                    b"< "
                    + b" ".join(("%06x" % c).encode("ascii") for c in string)
                    + b" >"
                )
            else:
                try:
                    string = string.encode("ascii")
                except UnicodeEncodeError:
                    string = b"\xfe\xff" + string.encode("utf-16-be")
                # We should probably encode more here because at least
                # ghostscript interpretes a carriage return byte (0x0D) as a
                # new line byte (0x0A)
                # PDF supports: \n, \r, \t, \b and \f
                string = string.replace(b"\\", b"\\\\")
                string = string.replace(b"(", b"\\(")
                string = string.replace(b")", b"\\)")
                return b"(" + string + b")"


else:

    class MyPdfString(object):
        @classmethod
        def encode(cls, string, hextype=False):
            if hextype:
                return (
                    b"< "
                    + b" ".join(("%06x" % c).encode("ascii") for c in string)
                    + b" >"
                )
            else:
                # This mimics exactely to what pdfrw does.
                string = string.replace(b"\\", b"\\\\")
                string = string.replace(b"(", b"\\(")
                string = string.replace(b")", b"\\)")
                return b"(" + string + b")"


class pdfdoc(object):
    def __init__(
        self,
        version="1.3",
        title=None,
        author=None,
        creator=None,
        producer=None,
        creationdate=None,
        moddate=None,
        subject=None,
        keywords=None,
        nodate=False,
        panes=None,
        initial_page=None,
        magnification=None,
        page_layout=None,
        fit_window=False,
        center_window=False,
        fullscreen=False,
        with_pdfrw=False,
    ):
        if with_pdfrw:
            try:
                from pdfrw import PdfWriter, PdfDict, PdfName, PdfString

                self.with_pdfrw = True
            except ImportError:
                PdfWriter = MyPdfWriter
                PdfDict = MyPdfDict
                PdfName = MyPdfName
                PdfString = MyPdfString
                self.with_pdfrw = False
        else:
            PdfWriter = MyPdfWriter
            PdfDict = MyPdfDict
            PdfName = MyPdfName
            PdfString = MyPdfString
            self.with_pdfrw = False

        now = datetime.now()
        self.info = PdfDict(indirect=True)

        def datetime_to_pdfdate(dt):
            return dt.strftime("%Y%m%d%H%M%SZ")

        if title is not None:
            self.info[PdfName.Title] = PdfString.encode(title)
        if author is not None:
            self.info[PdfName.Author] = PdfString.encode(author)
        if creator is not None:
            self.info[PdfName.Creator] = PdfString.encode(creator)
        if producer is not None and producer != "":
            self.info[PdfName.Producer] = PdfString.encode(producer)
        if creationdate is not None:
            self.info[PdfName.CreationDate] = PdfString.encode(
                "D:" + datetime_to_pdfdate(creationdate)
            )
        elif not nodate:
            self.info[PdfName.CreationDate] = PdfString.encode(
                "D:" + datetime_to_pdfdate(now)
            )
        if moddate is not None:
            self.info[PdfName.ModDate] = PdfString.encode(
                "D:" + datetime_to_pdfdate(moddate)
            )
        elif not nodate:
            self.info[PdfName.ModDate] = PdfString.encode(
                "D:" + datetime_to_pdfdate(now)
            )
        if subject is not None:
            self.info[PdfName.Subject] = PdfString.encode(subject)
        if keywords is not None:
            self.info[PdfName.Keywords] = PdfString.encode(",".join(keywords))

        self.writer = PdfWriter()
        self.writer.version = version
        # this is done because pdfrw adds info, catalog and pages as the first
        # three objects in this order
        if not self.with_pdfrw:
            self.writer.addobj(self.info)
            self.writer.addobj(self.writer.catalog)
            self.writer.addobj(self.writer.pages)

        self.panes = panes
        self.initial_page = initial_page
        self.magnification = magnification
        self.page_layout = page_layout
        self.fit_window = fit_window
        self.center_window = center_window
        self.fullscreen = fullscreen

    def add_imagepage(
        self,
        color,
        imgwidthpx,
        imgheightpx,
        imgformat,
        imgdata,
        imgwidthpdf,
        imgheightpdf,
        imgxpdf,
        imgypdf,
        pagewidth,
        pageheight,
        userunit=None,
        palette=None,
        inverted=False,
        depth=0,
        rotate=0,
        cropborder=None,
        bleedborder=None,
        trimborder=None,
        artborder=None,
    ):
        if self.with_pdfrw:
            from pdfrw import PdfDict, PdfName, PdfObject, PdfString
            from pdfrw.py23_diffs import convert_load
        else:
            PdfDict = MyPdfDict
            PdfName = MyPdfName
            PdfObject = MyPdfObject
            PdfString = MyPdfString
            convert_load = my_convert_load

        if color == Colorspace["1"] or color == Colorspace.L:
            colorspace = PdfName.DeviceGray
        elif color == Colorspace.RGB:
            colorspace = PdfName.DeviceRGB
        elif color == Colorspace.CMYK or color == Colorspace["CMYK;I"]:
            colorspace = PdfName.DeviceCMYK
        elif color == Colorspace.P:
            if self.with_pdfrw:
                raise Exception(
                    "pdfrw does not support hex strings for "
                    "palette image input, re-run with "
                    "--without-pdfrw"
                )
            colorspace = [
                PdfName.Indexed,
                PdfName.DeviceRGB,
                len(palette) - 1,
                PdfString.encode(palette, hextype=True),
            ]
        else:
            raise UnsupportedColorspaceError("unsupported color space: %s" % color.name)

        # either embed the whole jpeg or deflate the bitmap representation
        if imgformat is ImageFormat.JPEG:
            ofilter = PdfName.DCTDecode
        elif imgformat is ImageFormat.JPEG2000:
            ofilter = PdfName.JPXDecode
            self.writer.version = "1.5"  # jpeg2000 needs pdf 1.5
        elif imgformat is ImageFormat.CCITTGroup4:
            ofilter = [PdfName.CCITTFaxDecode]
        else:
            ofilter = PdfName.FlateDecode

        image = PdfDict(stream=convert_load(imgdata))

        image[PdfName.Type] = PdfName.XObject
        image[PdfName.Subtype] = PdfName.Image
        image[PdfName.Filter] = ofilter
        image[PdfName.Width] = imgwidthpx
        if (imgheightpx < 0):
            image[PdfName.Height] = -imgheightpx
        else:
            image[PdfName.Height] = imgheightpx
        image[PdfName.ColorSpace] = colorspace
        image[PdfName.BitsPerComponent] = depth

        if color == Colorspace["CMYK;I"]:
            # Inverts all four channels
            image[PdfName.Decode] = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]

        if imgformat is ImageFormat.CCITTGroup4:
            decodeparms = PdfDict()
            # The default for the K parameter is 0 which indicates Group 3 1-D
            # encoding. We set it to -1 because we want Group 4 encoding.
            decodeparms[PdfName.K] = -1
            if inverted:
                decodeparms[PdfName.BlackIs1] = PdfObject("false")
            else:
                decodeparms[PdfName.BlackIs1] = PdfObject("true")
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.Rows] = imgheightpx
            image[PdfName.DecodeParms] = [decodeparms]
        elif imgformat is ImageFormat.PBM:
            decodeparms = PdfDict()
            decodeparms[PdfName.Predictor] = 1
            decodeparms[PdfName.Colors] = 1
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.BitsPerComponent] = depth
            image[PdfName.DecodeParms] = decodeparms
        elif imgformat is ImageFormat.PNG:
            decodeparms = PdfDict()
            decodeparms[PdfName.Predictor] = 15
            if color in [Colorspace.P, Colorspace["1"], Colorspace.L]:
                decodeparms[PdfName.Colors] = 1
            else:
                decodeparms[PdfName.Colors] = 3
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.BitsPerComponent] = depth
            image[PdfName.DecodeParms] = decodeparms

        text = (
            "q\n%0.4f 0 0 %0.4f %0.4f %0.4f cm\n/Im0 Do\nQ"
            % (imgwidthpdf, -imgheightpdf, imgxpdf, imgypdf)
        ).encode("ascii")

        content = PdfDict(stream=convert_load(text))
        resources = PdfDict(XObject=PdfDict(Im0=image))

        page = PdfDict(indirect=True)
        page[PdfName.Type] = PdfName.Page
        page[PdfName.MediaBox] = [0, 0, pagewidth, pageheight]
        # 14.11.2 Page Boundaries
        # ...
        # The crop, bleed, trim, and art boxes shall not ordinarily extend
        # beyond the boundaries of the media box. If they do, they are
        # effectively reduced to their intersection with the media box.
        if cropborder is not None:
            page[PdfName.CropBox] = [
                cropborder[1],
                cropborder[0],
                pagewidth - 2 * cropborder[1],
                pageheight - 2 * cropborder[0],
            ]
        if bleedborder is None:
            if PdfName.CropBox in page:
                page[PdfName.BleedBox] = page[PdfName.CropBox]
        else:
            page[PdfName.BleedBox] = [
                bleedborder[1],
                bleedborder[0],
                pagewidth - 2 * bleedborder[1],
                pageheight - 2 * bleedborder[0],
            ]
        if trimborder is None:
            if PdfName.CropBox in page:
                page[PdfName.TrimBox] = page[PdfName.CropBox]
        else:
            page[PdfName.TrimBox] = [
                trimborder[1],
                trimborder[0],
                pagewidth - 2 * trimborder[1],
                pageheight - 2 * trimborder[0],
            ]
        if artborder is None:
            if PdfName.CropBox in page:
                page[PdfName.ArtBox] = page[PdfName.CropBox]
        else:
            page[PdfName.ArtBox] = [
                artborder[1],
                artborder[0],
                pagewidth - 2 * artborder[1],
                pageheight - 2 * artborder[0],
            ]
        page[PdfName.Resources] = resources
        page[PdfName.Contents] = content
        if rotate != 0:
            page[PdfName.Rotate] = rotate
        if userunit is not None:
            # /UserUnit requires PDF 1.6
            if self.writer.version < "1.6":
                self.writer.version = "1.6"
            page[PdfName.UserUnit] = userunit

        self.writer.addpage(page)

        if not self.with_pdfrw:
            self.writer.addobj(content)
            self.writer.addobj(image)

    def add_multi_imagepage(
        self,
        coordinates,
        collected_images
    ):
        (
            color,
            ndpi,
            imgformat,
            imgdata,
            imgwidthpx,
            imgheightpx,
            palette,
            inverted,
            depth,
            rotate,
        ) = collected_images[0]

        pagewidth, pageheight, imgwidthpdf, imgheightpdf = default_layout_fun(
            imgwidthpx, imgheightpx, ndpi
        )
        if (pageheight < 0):
            pageheight = -pageheight

        userunit = None
        if pagewidth < 3.00 or pageheight < 3.00:
            logging.warning(
                "pdf width or height is below 3.00 - too small for some viewers!"
            )
        elif pagewidth > 14400.0 or pageheight > 14400.0:
            if kwargs["allow_oversized"]:
                userunit = find_scale(pagewidth, pageheight)
                pagewidth /= userunit
                pageheight /= userunit
                imgwidthpdf /= userunit
                imgheightpdf /= userunit
            else:
                raise PdfTooLargeError(
                    "pdf width or height must not exceed 200 inches."
                )
        # the image is always centered on the page
        imgxpdf = (pagewidth - imgwidthpdf) / 2.0
        imgypdf = (pageheight + imgheightpdf) / 2.0

        cropborder=None
        bleedborder=None
        trimborder=None
        artborder=None

        if self.with_pdfrw:
            from pdfrw import PdfDict, PdfName, PdfObject, PdfString
            from pdfrw.py23_diffs import convert_load
        else:
            PdfDict = MyPdfDict
            PdfName = MyPdfName
            PdfObject = MyPdfObject
            PdfString = MyPdfString
            convert_load = my_convert_load

        if color == Colorspace["1"] or color == Colorspace.L:
            colorspace = PdfName.DeviceGray
        elif color == Colorspace.RGB:
            colorspace = PdfName.DeviceRGB
        elif color == Colorspace.CMYK or color == Colorspace["CMYK;I"]:
            colorspace = PdfName.DeviceCMYK
        elif color == Colorspace.P:
            if self.with_pdfrw:
                raise Exception(
                    "pdfrw does not support hex strings for "
                    "palette image input, re-run with "
                    "--without-pdfrw"
                )
            colorspace = [
                PdfName.Indexed,
                PdfName.DeviceRGB,
                len(palette) - 1,
                PdfString.encode(palette, hextype=True),
            ]
        else:
            raise UnsupportedColorspaceError("unsupported color space: %s" % color.name)

        # either embed the whole jpeg or deflate the bitmap representation
        if imgformat is ImageFormat.JPEG:
            ofilter = PdfName.DCTDecode
        elif imgformat is ImageFormat.JPEG2000:
            ofilter = PdfName.JPXDecode
            self.writer.version = "1.5"  # jpeg2000 needs pdf 1.5
        elif imgformat is ImageFormat.CCITTGroup4:
            ofilter = [PdfName.CCITTFaxDecode]
        else:
            ofilter = PdfName.FlateDecode

        image = PdfDict(stream=convert_load(imgdata))

        image[PdfName.Type] = PdfName.XObject
        image[PdfName.Subtype] = PdfName.Image
        image[PdfName.Filter] = ofilter
        image[PdfName.Width] = imgwidthpx
        if (imgheightpx < 0):
            image[PdfName.Height] = -imgheightpx
        else:
            image[PdfName.Height] = imgheightpx
        image[PdfName.ColorSpace] = colorspace
        image[PdfName.BitsPerComponent] = depth

        if color == Colorspace["CMYK;I"]:
            # Inverts all four channels
            image[PdfName.Decode] = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]

        if imgformat is ImageFormat.CCITTGroup4:
            decodeparms = PdfDict()
            # The default for the K parameter is 0 which indicates Group 3 1-D
            # encoding. We set it to -1 because we want Group 4 encoding.
            decodeparms[PdfName.K] = -1
            if inverted:
                decodeparms[PdfName.BlackIs1] = PdfObject("false")
            else:
                decodeparms[PdfName.BlackIs1] = PdfObject("true")
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.Rows] = imgheightpx
            image[PdfName.DecodeParms] = [decodeparms]
        elif imgformat is ImageFormat.PBM:
            decodeparms = PdfDict()
            decodeparms[PdfName.Predictor] = 1
            decodeparms[PdfName.Colors] = 1
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.BitsPerComponent] = depth
            image[PdfName.DecodeParms] = decodeparms
        elif imgformat is ImageFormat.PNG:
            decodeparms = PdfDict()
            decodeparms[PdfName.Predictor] = 15
            if color in [Colorspace.P, Colorspace["1"], Colorspace.L]:
                decodeparms[PdfName.Colors] = 1
            else:
                decodeparms[PdfName.Colors] = 3
            decodeparms[PdfName.Columns] = imgwidthpx
            decodeparms[PdfName.BitsPerComponent] = depth
            image[PdfName.DecodeParms] = decodeparms

        text = (
            "q\n%0.4f 0 0 %0.4f %0.4f %0.4f cm\n/Im0 Do\nQ"
            % (imgwidthpdf, -imgheightpdf, imgxpdf, imgypdf)
        ).encode("ascii")

        image_dict = PdfDict(Im0=image)
        secondary_images = []
        for i in range(len(collected_images)):
            if i == 0:
                # skip main image
                continue
            Im_i ={}
            (
                Im_i['color'],
                Im_i['ndpi'],
                Im_i['imgformat'],
                Im_i['imgdata'],
                Im_i['imgwidthpx'],
                Im_i['imgheightpx'],
                Im_i['palette'],
                Im_i['inverted'],
                Im_i['depth'],
                Im_i['rotate'],
            ) = collected_images[i]
            Im_i['pagewidth'], Im_i['pageheight'], Im_i['imgwidthpdf'], Im_i['imgheightpdf'] = default_layout_fun(
                Im_i['imgwidthpx'], Im_i['imgheightpx'], Im_i['ndpi']
            )
            Im_i['imgxpdf'] = (Im_i['pagewidth'] - Im_i['imgwidthpdf']) / 2.0
            Im_i['imgypdf'] = (Im_i['pageheight'] + Im_i['imgheightpdf']) / 2.0

            ofilter = PdfName.DCTDecode

            image1 = PdfDict(stream=convert_load(Im_i['imgdata']))

            image1[PdfName.Type] = PdfName.XObject
            image1[PdfName.Subtype] = PdfName.Image
            image1[PdfName.Filter] = ofilter
            image1[PdfName.Width] = Im_i['imgwidthpx']
            if (Im_i['imgheightpx'] < 0):
                image1[PdfName.Height] = -Im_i['imgheightpx']
            else:
                image1[PdfName.Height] = Im_i['imgheightpx']
            if Im_i['color'] == Colorspace.L:
                image1[PdfName.ColorSpace] = PdfName.DeviceGray
            else:
                image1[PdfName.ColorSpace] = PdfName.DeviceRGB
            image1[PdfName.BitsPerComponent] = Im_i['depth']

            offset_x = coordinates[i][0] / 300 * 72 / 2.473
            offset_y = coordinates[i][1] / 300 * 72 / 2.473

            if (Im_i['imgheightpx'] < 0):
                offset_y -= Im_i['imgheightpdf']

            text += (
                "\nq\n%0.4f 0 0 %0.4f %0.4f %0.4f cm\n/Im%d Do\nQ"
                % (Im_i['imgwidthpdf'], -Im_i['imgheightpdf'], offset_x, imgypdf - offset_y, i)
            ).encode("ascii")
            image_dict[b'/Im%d' % i]=image1
            secondary_images.append(image1)

        content = PdfDict(stream=convert_load(text))
        resources = PdfDict(XObject=image_dict)

        page = PdfDict(indirect=True)
        page[PdfName.Type] = PdfName.Page
        page[PdfName.MediaBox] = [0, 0, pagewidth, pageheight]
        # 14.11.2 Page Boundaries
        # ...
        # The crop, bleed, trim, and art boxes shall not ordinarily extend
        # beyond the boundaries of the media box. If they do, they are
        # effectively reduced to their intersection with the media box.
        if cropborder is not None:
            page[PdfName.CropBox] = [
                cropborder[1],
                cropborder[0],
                pagewidth - 2 * cropborder[1],
                pageheight - 2 * cropborder[0],
            ]
        if bleedborder is None:
            if PdfName.CropBox in page:
                page[PdfName.BleedBox] = page[PdfName.CropBox]
        else:
            page[PdfName.BleedBox] = [
                bleedborder[1],
                bleedborder[0],
                pagewidth - 2 * bleedborder[1],
                pageheight - 2 * bleedborder[0],
            ]
        if trimborder is None:
            if PdfName.CropBox in page:
                page[PdfName.TrimBox] = page[PdfName.CropBox]
        else:
            page[PdfName.TrimBox] = [
                trimborder[1],
                trimborder[0],
                pagewidth - 2 * trimborder[1],
                pageheight - 2 * trimborder[0],
            ]
        if artborder is None:
            if PdfName.CropBox in page:
                page[PdfName.ArtBox] = page[PdfName.CropBox]
        else:
            page[PdfName.ArtBox] = [
                artborder[1],
                artborder[0],
                pagewidth - 2 * artborder[1],
                pageheight - 2 * artborder[0],
            ]
        page[PdfName.Resources] = resources
        page[PdfName.Contents] = content
        if rotate != 0:
            page[PdfName.Rotate] = rotate
        if userunit is not None:
            # /UserUnit requires PDF 1.6
            if self.writer.version < "1.6":
                self.writer.version = "1.6"
            page[PdfName.UserUnit] = userunit

        self.writer.addpage(page)

        if not self.with_pdfrw:
            self.writer.addobj(content)
            self.writer.addobj(image)
            for im in secondary_images:
                self.writer.addobj(im)

    def tostring(self):
        stream = BytesIO()
        self.tostream(stream)
        return stream.getvalue()

    def tostream(self, outputstream):
        if self.with_pdfrw:
            from pdfrw import PdfDict, PdfName, PdfArray, PdfObject
        else:
            PdfDict = MyPdfDict
            PdfName = MyPdfName
            PdfObject = MyPdfObject
            PdfArray = MyPdfArray
        NullObject = PdfObject("null")
        TrueObject = PdfObject("true")

        # We fill the catalog with more information like /ViewerPreferences,
        # /PageMode, /PageLayout or /OpenAction because the latter refers to a
        # page object which has to be present so that we can get its id.
        #
        # Furthermore, if using pdfrw, the trailer is cleared every time a page
        # is added, so we can only start using it after all pages have been
        # written.

        if self.with_pdfrw:
            catalog = self.writer.trailer.Root
        else:
            catalog = self.writer.catalog

        if (
            self.fullscreen
            or self.fit_window
            or self.center_window
            or self.panes is not None
        ):
            catalog[PdfName.ViewerPreferences] = PdfDict()

        if self.fullscreen:
            # this setting might be overwritten later by the page mode
            catalog[PdfName.ViewerPreferences][
                PdfName.NonFullScreenPageMode
            ] = PdfName.UseNone

        if self.panes == PageMode.thumbs:
            catalog[PdfName.ViewerPreferences][
                PdfName.NonFullScreenPageMode
            ] = PdfName.UseThumbs
            # this setting might be overwritten later if fullscreen
            catalog[PdfName.PageMode] = PdfName.UseThumbs
        elif self.panes == PageMode.outlines:
            catalog[PdfName.ViewerPreferences][
                PdfName.NonFullScreenPageMode
            ] = PdfName.UseOutlines
            # this setting might be overwritten later if fullscreen
            catalog[PdfName.PageMode] = PdfName.UseOutlines
        elif self.panes in [PageMode.none, None]:
            pass
        else:
            raise ValueError("unknown page mode: %s" % self.panes)

        if self.fit_window:
            catalog[PdfName.ViewerPreferences][PdfName.FitWindow] = TrueObject

        if self.center_window:
            catalog[PdfName.ViewerPreferences][PdfName.CenterWindow] = TrueObject

        if self.fullscreen:
            catalog[PdfName.PageMode] = PdfName.FullScreen

        # see table 8.2 in section 8.2.1 in
        # http://partners.adobe.com/public/developer/en/pdf/PDFReference16.pdf
        # Fit - Fits the page to the window.
        # FitH - Fits the width of the page to the window.
        # FitV - Fits the height of the page to the window.
        # FitR - Fits the rectangle specified by the four coordinates to the
        #        window.
        # FitB - Fits the page bounding box to the window. This basically
        #        reduces the amount of whitespace (margins) that is displayed
        #        and thus focussing more on the text content.
        # FitBH - Fits the width of the page bounding box to the window.
        # FitBV - Fits the height of the page bounding box to the window.

        # by default the initial page is the first one
        initial_page = self.writer.pagearray[0]
        # we set the open action here to make sure we open on the requested
        # initial page but this value might be overwritten by a custom open
        # action later while still taking the requested initial page into
        # account
        if self.initial_page is not None:
            initial_page = self.writer.pagearray[self.initial_page - 1]
            catalog[PdfName.OpenAction] = PdfArray(
                [initial_page, PdfName.XYZ, NullObject, NullObject, 0]
            )

        if self.magnification == Magnification.fit:
            catalog[PdfName.OpenAction] = PdfArray([initial_page, PdfName.Fit])
        elif self.magnification == Magnification.fith:
            pagewidth = initial_page[PdfName.MediaBox][2]
            catalog[PdfName.OpenAction] = PdfArray(
                [initial_page, PdfName.FitH, pagewidth]
            )
        elif self.magnification == Magnification.fitbh:
            # quick hack to determine the image width on the page
            imgwidth = float(initial_page[PdfName.Contents].stream.split()[4])
            catalog[PdfName.OpenAction] = PdfArray(
                [initial_page, PdfName.FitBH, imgwidth]
            )
        elif isinstance(self.magnification, float):
            catalog[PdfName.OpenAction] = PdfArray(
                [initial_page, PdfName.XYZ, NullObject, NullObject, self.magnification]
            )
        elif self.magnification is None:
            pass
        else:
            raise ValueError("unknown magnification: %s" % self.magnification)

        if self.page_layout == PageLayout.single:
            catalog[PdfName.PageLayout] = PdfName.SinglePage
        elif self.page_layout == PageLayout.onecolumn:
            catalog[PdfName.PageLayout] = PdfName.OneColumn
        elif self.page_layout == PageLayout.twocolumnright:
            catalog[PdfName.PageLayout] = PdfName.TwoColumnRight
        elif self.page_layout == PageLayout.twocolumnleft:
            catalog[PdfName.PageLayout] = PdfName.TwoColumnLeft
        elif self.page_layout is None:
            pass
        else:
            raise ValueError("unknown page layout: %s" % self.page_layout)

        # now write out the PDF
        if self.with_pdfrw:
            self.writer.trailer.Info = self.info
            self.writer.write(outputstream)
        else:
            self.writer.tostream(self.info, outputstream)


def get_imgmetadata(imgdata, imgformat, default_dpi, colorspace, rawdata=None):
    if imgformat == ImageFormat.JPEG2000 and rawdata is not None and imgdata is None:
        # this codepath gets called if the PIL installation is not able to
        # handle JPEG2000 files
        imgwidthpx, imgheightpx, ics, hdpi, vdpi = parsejp2(rawdata)

        if hdpi is None:
            hdpi = default_dpi
        if vdpi is None:
            vdpi = default_dpi
        ndpi = (hdpi, vdpi)
    else:
        imgwidthpx, imgheightpx = imgdata.size

        ndpi = imgdata.info.get("dpi", (default_dpi, default_dpi))
        # In python3, the returned dpi value for some tiff images will
        # not be an integer but a float. To make the behaviour of
        # img2pdf the same between python2 and python3, we convert that
        # float into an integer by rounding.
        # Search online for the 72.009 dpi problem for more info.
        ndpi = (int(round(ndpi[0])), int(round(ndpi[1])))
        ics = imgdata.mode

    if ics in ["LA", "PA", "RGBA"] or "transparency" in imgdata.info:
        logging.warning("Image contains transparency which cannot be retained in PDF.")
        logging.warning("img2pdf will not perform a lossy operation.")
        logging.warning("You can remove the alpha channel using imagemagick:")
        logging.warning(
            "  $ convert input.png -background white -alpha "
            "remove -alpha off output.png"
        )
        raise AlphaChannelError("Refusing to work on images with alpha channel")

    # Since commit 07a96209597c5e8dfe785c757d7051ce67a980fb or release 4.1.0
    # Pillow retrieves the DPI from EXIF if it cannot find the DPI in the JPEG
    # header. In that case it can happen that the horizontal and vertical DPI
    # are set to zero.
    if ndpi == (0, 0):
        ndpi = (default_dpi, default_dpi)

    # PIL defaults to a dpi of 1 if a TIFF image does not specify the dpi.
    # In that case, we want to use a different default.
    if ndpi == (1, 1) and imgformat == ImageFormat.TIFF:
        ndpi = (
            imgdata.tag_v2.get(TiffImagePlugin.X_RESOLUTION, default_dpi),
            imgdata.tag_v2.get(TiffImagePlugin.Y_RESOLUTION, default_dpi),
        )

    logging.debug("input dpi = %d x %d", *ndpi)

    rotation = 0
    if hasattr(imgdata, "_getexif") and imgdata._getexif() is not None:
        for tag, value in imgdata._getexif().items():
            if TAGS.get(tag, tag) == "Orientation":
                # Detailed information on EXIF rotation tags:
                # http://impulseadventure.com/photo/exif-orientation.html
                if value == 1:
                    rotation = 0
                elif value == 6:
                    rotation = 90
                elif value == 3:
                    rotation = 180
                elif value == 8:
                    rotation = 270
                elif value in (2, 4, 5, 7):
                    raise ExifOrientationError(
                        "Unsupported flipped rotation mode (%d)" % value
                    )
                else:
                    raise ExifOrientationError("Invalid rotation (%d)" % value)

    logging.debug("rotation = %d°", rotation)

    if colorspace:
        color = colorspace
        logging.debug("input colorspace (forced) = %s", color)
    else:
        color = None
        for c in Colorspace:
            if c.name == ics:
                color = c
        if color is None:
            # PIL does not provide the information about the original
            # colorspace for 16bit grayscale PNG images. Thus, we retrieve
            # that info manually by looking at byte 10 in the IHDR chunk. We
            # know where to find that in the file because the IHDR chunk must
            # be the first chunk
            if (
                rawdata is not None
                and imgformat == ImageFormat.PNG
                and rawdata[25] == 0
            ):
                color = Colorspace.L
            else:
                raise ValueError("unknown colorspace")
        if color == Colorspace.CMYK and imgformat == ImageFormat.JPEG:
            # Adobe inverts CMYK JPEGs for some reason, and others
            # have followed suit as well. Some software assumes the
            # JPEG is inverted if the Adobe tag (APP14), while other
            # software assumes all CMYK JPEGs are inverted. I don't
            # have enough experience with these to know which is
            # better for images currently in the wild, so I'm going
            # with the first approach for now.
            if "adobe" in imgdata.info:
                color = Colorspace["CMYK;I"]
        logging.debug("input colorspace = %s", color.name)

    logging.debug("width x height = %dpx x %dpx", imgwidthpx, imgheightpx)

    return (color, ndpi, imgwidthpx, imgheightpx, rotation)


def ccitt_payload_location_from_pil(img):
    # If Pillow is passed an invalid compression argument it will ignore it;
    # make sure the image actually got compressed.
    if img.info["compression"] != "group4":
        raise ValueError(
            "Image not compressed with CCITT Group 4 but with: %s"
            % img.info["compression"]
        )

    # Read the TIFF tags to find the offset(s) of the compressed data strips.
    strip_offsets = img.tag_v2[TiffImagePlugin.STRIPOFFSETS]
    strip_bytes = img.tag_v2[TiffImagePlugin.STRIPBYTECOUNTS]
    rows_per_strip = img.tag_v2.get(TiffImagePlugin.ROWSPERSTRIP, 2 ** 32 - 1)

    # PIL always seems to create a single strip even for very large TIFFs when
    # it saves images, so assume we only have to read a single strip.
    # A test ~10 GPixel image was still encoded as a single strip. Just to be
    # safe check throw an error if there is more than one offset.
    if len(strip_offsets) != 1 or len(strip_bytes) != 1:
        raise NotImplementedError("Transcoding multiple strips not supported")

    (offset,), (length,) = strip_offsets, strip_bytes

    logging.debug("TIFF strip_offsets: %d" % offset)
    logging.debug("TIFF strip_bytes: %d" % length)

    return offset, length


def transcode_monochrome(imgdata):
    """Convert the open PIL.Image imgdata to compressed CCITT Group4 data"""

    logging.debug("Converting monochrome to CCITT Group4")

    # Convert the image to Group 4 in memory. If libtiff is not installed and
    # Pillow is not compiled against it, .save() will raise an exception.
    newimgio = BytesIO()

    # we create a whole new PIL image or otherwise it might happen with some
    # input images, that libtiff fails an assert and the whole process is
    # killed by a SIGABRT:
    #   https://gitlab.mister-muffin.de/josch/img2pdf/issues/46
    im = Image.frombytes(imgdata.mode, imgdata.size, imgdata.tobytes())
    im.save(newimgio, format="TIFF", compression="group4")

    # Open new image in memory
    newimgio.seek(0)
    newimg = Image.open(newimgio)

    offset, length = ccitt_payload_location_from_pil(newimg)

    newimgio.seek(offset)
    return newimgio.read(length)


def parse_png(rawdata):
    pngidat = b""
    palette = []
    i = 16
    while i < len(rawdata):
        # once we can require Python >= 3.2 we can use int.from_bytes() instead
        n, = struct.unpack(">I", rawdata[i - 8 : i - 4])
        if i + n > len(rawdata):
            raise Exception("invalid png: %d %d %d" % (i, n, len(rawdata)))
        if rawdata[i - 4 : i] == b"IDAT":
            pngidat += rawdata[i : i + n]
        elif rawdata[i - 4 : i] == b"PLTE":
            # This could be as simple as saying "palette = rawdata[i:i+n]" but
            # pdfrw does only escape parenthesis and backslashes in the raw
            # byte stream. But raw carriage return bytes are interpreted as
            # line feed bytes by ghostscript. So instead we use the hex string
            # format. pdfrw cannot write it but at least ghostscript is happy
            # with it. We would also write out the palette in binary format
            # (and escape more bytes) but since we cannot use pdfrw anyways,
            # we choose the more human readable variant.
            # See https://github.com/pmaupin/pdfrw/issues/147
            for j in range(i, i + n, 3):
                # with int.from_bytes() we would not have to prepend extra
                # zeroes
                color, = struct.unpack(">I", b"\x00" + rawdata[j : j + 3])
                palette.append(color)
        i += n
        i += 12
    return pngidat, palette


def read_images(rawdata, colorspace, first_frame_only=False):
    im = BytesIO(rawdata)
    im.seek(0)
    imgdata = None
    try:
        imgdata = Image.open(im)
    except IOError as e:
        # test if it is a jpeg2000 image
        if rawdata[:12] != b"\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A":
            raise ImageOpenError(
                "cannot read input image (not jpeg2000). "
                "PIL: error reading image: %s" % e
            )
        # image is jpeg2000
        imgformat = ImageFormat.JPEG2000
    else:
        imgformat = None
        for f in ImageFormat:
            if f.name == imgdata.format:
                imgformat = f
        if imgformat is None:
            imgformat = ImageFormat.other

    logging.debug("imgformat = %s", imgformat.name)

    # depending on the input format, determine whether to pass the raw
    # image or the zlib compressed color information

    # JPEG and JPEG2000 can be embedded into the PDF as-is
    if imgformat == ImageFormat.JPEG or imgformat == ImageFormat.JPEG2000:
        color, ndpi, imgwidthpx, imgheightpx, rotation = get_imgmetadata(
            imgdata, imgformat, default_dpi, colorspace, rawdata
        )
        if color == Colorspace["1"]:
            raise JpegColorspaceError("jpeg can't be monochrome")
        if color == Colorspace["P"]:
            raise JpegColorspaceError("jpeg can't have a color palette")
        if color == Colorspace["RGBA"]:
            raise JpegColorspaceError("jpeg can't have an alpha channel")
        im.close()
        logging.debug("read_images() embeds a JPEG")
        return [
            (
                color,
                ndpi,
                imgformat,
                rawdata,
                imgwidthpx,
                imgheightpx,
                [],
                False,
                8,
                rotation,
            )
        ]

    # We can directly embed the IDAT chunk of PNG images if the PNG is not
    # interlaced
    #
    # PIL does not provide the information whether a PNG was stored interlaced
    # or not. Thus, we retrieve that info manually by looking at byte 13 in the
    # IHDR chunk. We know where to find that in the file because the IHDR chunk
    # must be the first chunk.
    if imgformat == ImageFormat.PNG and rawdata[28] == 0:
        color, ndpi, imgwidthpx, imgheightpx, rotation = get_imgmetadata(
            imgdata, imgformat, default_dpi, colorspace, rawdata
        )
        pngidat, palette = parse_png(rawdata)
        im.close()
        # PIL does not provide the information about the original bits per
        # sample. Thus, we retrieve that info manually by looking at byte 9 in
        # the IHDR chunk. We know where to find that in the file because the
        # IHDR chunk must be the first chunk
        depth = rawdata[24]
        if depth not in [1, 2, 4, 8, 16]:
            raise ValueError("invalid bit depth: %d" % depth)
        logging.debug("read_images() embeds a PNG")
        return [
            (
                color,
                ndpi,
                imgformat,
                pngidat,
                imgwidthpx,
                imgheightpx,
                palette,
                False,
                depth,
                rotation,
            )
        ]

    # If our input is not JPEG or PNG, then we might have a format that
    # supports multiple frames (like TIFF or GIF), so we need a loop to
    # iterate through all frames of the image.
    #
    # Each frame gets compressed using PNG compression *except* if:
    #
    #  * The image is monochrome => encode using CCITT group 4
    #
    #  * The image is CMYK => zip plain RGB data
    #
    #  * We are handling a CCITT encoded TIFF frame => embed data

    result = []
    img_page_count = 0
    # loop through all frames of the image (example: multipage TIFF)
    while True:
        try:
            imgdata.seek(img_page_count)
        except EOFError:
            break

        if first_frame_only and img_page_count > 0:
            break

        # PIL is unable to preserve the data of 16-bit RGB TIFF files and will
        # convert it to 8-bit without the possibility to retrieve the original
        # data
        # https://github.com/python-pillow/Pillow/issues/1888
        #
        # Some tiff images do not have BITSPERSAMPLE set. Use this to create
        # such a tiff: tiffset -u 258 test.tif
        if (
            imgformat == ImageFormat.TIFF
            and max(imgdata.tag_v2.get(TiffImagePlugin.BITSPERSAMPLE, [1])) > 8
        ):
            raise ValueError("PIL is unable to preserve more than 8 bits per sample")

        # We can directly copy the data out of a CCITT Group 4 encoded TIFF, if it
        # only contains a single strip
        if (
            imgformat == ImageFormat.TIFF
            and imgdata.info["compression"] == "group4"
            and len(imgdata.tag_v2[TiffImagePlugin.STRIPOFFSETS]) == 1
        ):
            photo = imgdata.tag_v2[TiffImagePlugin.PHOTOMETRIC_INTERPRETATION]
            inverted = False
            if photo == 0:
                inverted = True
            elif photo != 1:
                raise ValueError(
                    "unsupported photometric interpretation for "
                    "group4 tiff: %d" % photo
                )
            color, ndpi, imgwidthpx, imgheightpx, rotation = get_imgmetadata(
                imgdata, imgformat, default_dpi, colorspace, rawdata
            )
            offset, length = ccitt_payload_location_from_pil(imgdata)
            im.seek(offset)
            rawdata = im.read(length)
            fillorder = imgdata.tag_v2.get(TiffImagePlugin.FILLORDER)
            if fillorder is None:
                # no FillOrder: nothing to do
                pass
            elif fillorder == 1:
                # msb-to-lsb: nothing to do
                pass
            elif fillorder == 2:
                logging.debug("fillorder is lsb-to-msb => reverse bits")
                # lsb-to-msb: reverse bits of each byte
                rawdata = bytearray(rawdata)
                for i in range(len(rawdata)):
                    rawdata[i] = TIFFBitRevTable[rawdata[i]]
                rawdata = bytes(rawdata)
            else:
                raise ValueError("unsupported FillOrder: %d" % fillorder)
            logging.debug("read_images() embeds Group4 from TIFF")
            result.append(
                (
                    color,
                    ndpi,
                    ImageFormat.CCITTGroup4,
                    rawdata,
                    imgwidthpx,
                    imgheightpx,
                    [],
                    inverted,
                    1,
                    rotation,
                )
            )
            img_page_count += 1
            continue

        logging.debug("Converting frame: %d" % img_page_count)

        color, ndpi, imgwidthpx, imgheightpx, rotation = get_imgmetadata(
            imgdata, imgformat, default_dpi, colorspace
        )

        newimg = None
        if color == Colorspace["1"]:
            if (rawdata[0:2] == b"P4"):
                zdata = zlib.compress(rawdata[13:])
            else:
                zdata = zlib.compress(rawdata)
            result.append(
                (
                    Colorspace.P,
                    ndpi,
                    ImageFormat.PBM,
                    zdata,
                    imgwidthpx,
                    imgheightpx,
                    [0xffffff, 0],
                    False,
                    1,
                    rotation,
                )
            )
            img_page_count += 1
            continue
        elif color in [
            Colorspace.RGB,
            Colorspace.L,
            Colorspace.CMYK,
            Colorspace["CMYK;I"],
            Colorspace.P,
        ]:
            logging.debug("Colorspace is OK: %s", color)
            newimg = imgdata
        else:
            raise ValueError("unknown or unsupported colorspace: %s" % color.name)
        # the PNG format does not support CMYK, so we fall back to normal
        # compression
        if color in [Colorspace.CMYK, Colorspace["CMYK;I"]]:
            imggz = zlib.compress(newimg.tobytes())
            logging.debug("read_images() encoded CMYK with flate compression")
            result.append(
                (
                    color,
                    ndpi,
                    imgformat,
                    imggz,
                    imgwidthpx,
                    imgheightpx,
                    [],
                    False,
                    8,
                    rotation,
                )
            )
        else:
            # cheapo version to retrieve a PNG encoding of the payload is to
            # just save it with PIL. In the future this could be replaced by
            # dedicated function applying the Paeth PNG filter to the raw pixel
            pngbuffer = BytesIO()
            newimg.save(pngbuffer, format="png")
            pngidat, palette = parse_png(pngbuffer.getvalue())
            # PIL does not provide the information about the original bits per
            # sample. Thus, we retrieve that info manually by looking at byte 9 in
            # the IHDR chunk. We know where to find that in the file because the
            # IHDR chunk must be the first chunk
            pngbuffer.seek(24)
            depth = ord(pngbuffer.read(1))
            if depth not in [1, 2, 4, 8, 16]:
                raise ValueError("invalid bit depth: %d" % depth)
            logging.debug("read_images() encoded an image as PNG")
            result.append(
                (
                    color,
                    ndpi,
                    ImageFormat.PNG,
                    pngidat,
                    imgwidthpx,
                    imgheightpx,
                    palette,
                    False,
                    depth,
                    rotation,
                )
            )
        img_page_count += 1
    # the python-pil version 2.3.0-1ubuntu3 in Ubuntu does not have the
    # close() method
    try:
        imgdata.close()
    except AttributeError:
        pass
    im.close()
    return result


# converts a length in pixels to a length in PDF units (1/72 of an inch)
def px_to_pt(length, dpi):
    return 72.0 * length / dpi


def cm_to_pt(length):
    return (72.0 * length) / 2.54


def mm_to_pt(length):
    return (72.0 * length) / 25.4


def in_to_pt(length):
    return 72.0 * length


def get_layout_fun(
    pagesize=None, imgsize=None, border=None, fit=None, auto_orient=False
):
    def fitfun(fit, imgwidth, imgheight, fitwidth, fitheight):
        if fitwidth is None and fitheight is None:
            raise ValueError("fitwidth and fitheight cannot both be None")
        # if fit is fill or enlarge then it is okay if one of the dimensions
        # are negative but one of them must still be positive
        # if fit is not fill or enlarge then both dimensions must be positive
        if (
            fit in [FitMode.fill, FitMode.enlarge]
            and fitwidth is not None
            and fitwidth < 0
            and fitheight is not None
            and fitheight < 0
        ):
            raise ValueError(
                "cannot fit into a rectangle where both dimensions are negative"
            )
        elif fit not in [FitMode.fill, FitMode.enlarge] and (
            (fitwidth is not None and fitwidth < 0)
            or (fitheight is not None and fitheight < 0)
        ):
            raise Exception(
                "cannot fit into a rectangle where either dimensions are negative"
            )

        def default():
            if fitwidth is not None and fitheight is not None:
                newimgwidth = fitwidth
                newimgheight = (newimgwidth * imgheight) / imgwidth
                if newimgheight > fitheight:
                    newimgheight = fitheight
                    newimgwidth = (newimgheight * imgwidth) / imgheight
            elif fitwidth is None and fitheight is not None:
                newimgheight = fitheight
                newimgwidth = (newimgheight * imgwidth) / imgheight
            elif fitheight is None and fitwidth is not None:
                newimgwidth = fitwidth
                newimgheight = (newimgwidth * imgheight) / imgwidth
            else:
                raise ValueError("fitwidth and fitheight cannot both be None")
            return newimgwidth, newimgheight

        if fit is None or fit == FitMode.into:
            return default()
        elif fit == FitMode.fill:
            if fitwidth is not None and fitheight is not None:
                newimgwidth = fitwidth
                newimgheight = (newimgwidth * imgheight) / imgwidth
                if newimgheight < fitheight:
                    newimgheight = fitheight
                    newimgwidth = (newimgheight * imgwidth) / imgheight
            elif fitwidth is None and fitheight is not None:
                newimgheight = fitheight
                newimgwidth = (newimgheight * imgwidth) / imgheight
            elif fitheight is None and fitwidth is not None:
                newimgwidth = fitwidth
                newimgheight = (newimgwidth * imgheight) / imgwidth
            else:
                raise ValueError("fitwidth and fitheight cannot both be None")
            return newimgwidth, newimgheight
        elif fit == FitMode.exact:
            if fitwidth is not None and fitheight is not None:
                return fitwidth, fitheight
            elif fitwidth is None and fitheight is not None:
                newimgheight = fitheight
                newimgwidth = (newimgheight * imgwidth) / imgheight
            elif fitheight is None and fitwidth is not None:
                newimgwidth = fitwidth
                newimgheight = (newimgwidth * imgheight) / imgwidth
            else:
                raise ValueError("fitwidth and fitheight cannot both be None")
            return newimgwidth, newimgheight
        elif fit == FitMode.shrink:
            if fitwidth is not None and fitheight is not None:
                if imgwidth <= fitwidth and imgheight <= fitheight:
                    return imgwidth, imgheight
            elif fitwidth is None and fitheight is not None:
                if imgheight <= fitheight:
                    return imgwidth, imgheight
            elif fitheight is None and fitwidth is not None:
                if imgwidth <= fitwidth:
                    return imgwidth, imgheight
            else:
                raise ValueError("fitwidth and fitheight cannot both be None")
            return default()
        elif fit == FitMode.enlarge:
            if fitwidth is not None and fitheight is not None:
                if imgwidth > fitwidth or imgheight > fitheight:
                    return imgwidth, imgheight
            elif fitwidth is None and fitheight is not None:
                if imgheight > fitheight:
                    return imgwidth, imgheight
            elif fitheight is None and fitwidth is not None:
                if imgwidth > fitwidth:
                    return imgwidth, imgheight
            else:
                raise ValueError("fitwidth and fitheight cannot both be None")
            return default()
        else:
            raise NotImplementedError

    # if no layout arguments are given, then the image size is equal to the
    # page size and will be drawn with the default dpi
    if pagesize is None and imgsize is None and border is None:
        return default_layout_fun
    if pagesize is None and imgsize is None and border is not None:

        def layout_fun(imgwidthpx, imgheightpx, ndpi):
            imgwidthpdf = px_to_pt(imgwidthpx, ndpi[0])
            imgheightpdf = px_to_pt(imgheightpx, ndpi[1])
            pagewidth = imgwidthpdf + 2 * border[1]
            pageheight = imgheightpdf + 2 * border[0]
            return pagewidth, pageheight, imgwidthpdf, imgheightpdf

        return layout_fun
    if border is None:
        border = (0, 0)
    # if the pagesize is given but the imagesize is not, then the imagesize
    # will be calculated from the pagesize, taking into account the border
    # and the fitting
    if pagesize is not None and imgsize is None:

        def layout_fun(imgwidthpx, imgheightpx, ndpi):
            if (
                pagesize[0] is not None
                and pagesize[1] is not None
                and auto_orient
                and (
                    (imgwidthpx > imgheightpx and pagesize[0] < pagesize[1])
                    or (imgwidthpx < imgheightpx and pagesize[0] > pagesize[1])
                )
            ):
                pagewidth, pageheight = pagesize[1], pagesize[0]
                newborder = border[1], border[0]
            else:
                pagewidth, pageheight = pagesize[0], pagesize[1]
                newborder = border
            if pagewidth is not None:
                fitwidth = pagewidth - 2 * newborder[1]
            else:
                fitwidth = None
            if pageheight is not None:
                fitheight = pageheight - 2 * newborder[0]
            else:
                fitheight = None
            if (
                fit in [FitMode.fill, FitMode.enlarge]
                and fitwidth is not None
                and fitwidth < 0
                and fitheight is not None
                and fitheight < 0
            ):
                raise NegativeDimensionError(
                    "at least one border dimension musts be smaller than half "
                    "the respective page dimension"
                )
            elif fit not in [FitMode.fill, FitMode.enlarge] and (
                (fitwidth is not None and fitwidth < 0)
                or (fitheight is not None and fitheight < 0)
            ):
                raise NegativeDimensionError(
                    "one border dimension is larger than half of the "
                    "respective page dimension"
                )
            imgwidthpdf, imgheightpdf = fitfun(
                fit,
                px_to_pt(imgwidthpx, ndpi[0]),
                px_to_pt(imgheightpx, ndpi[1]),
                fitwidth,
                fitheight,
            )
            if pagewidth is None:
                pagewidth = imgwidthpdf + border[1] * 2
            if pageheight is None:
                pageheight = imgheightpdf + border[0] * 2
            return pagewidth, pageheight, imgwidthpdf, imgheightpdf

        return layout_fun

    def scale_imgsize(s, px, dpi):
        if s is None:
            return None
        mode, value = s
        if mode == ImgSize.abs:
            return value
        if mode == ImgSize.perc:
            return (px_to_pt(px, dpi) * value) / 100
        if mode == ImgSize.dpi:
            return px_to_pt(px, value)
        raise NotImplementedError

    if pagesize is None and imgsize is not None:

        def layout_fun(imgwidthpx, imgheightpx, ndpi):
            imgwidthpdf, imgheightpdf = fitfun(
                fit,
                px_to_pt(imgwidthpx, ndpi[0]),
                px_to_pt(imgheightpx, ndpi[1]),
                scale_imgsize(imgsize[0], imgwidthpx, ndpi[0]),
                scale_imgsize(imgsize[1], imgheightpx, ndpi[1]),
            )
            pagewidth = imgwidthpdf + 2 * border[1]
            pageheight = imgheightpdf + 2 * border[0]
            return pagewidth, pageheight, imgwidthpdf, imgheightpdf

        return layout_fun
    if pagesize is not None and imgsize is not None:

        def layout_fun(imgwidthpx, imgheightpx, ndpi):
            if (
                pagesize[0] is not None
                and pagesize[1] is not None
                and auto_orient
                and (
                    (imgwidthpx > imgheightpx and pagesize[0] < pagesize[1])
                    or (imgwidthpx < imgheightpx and pagesize[0] > pagesize[1])
                )
            ):
                pagewidth, pageheight = pagesize[1], pagesize[0]
            else:
                pagewidth, pageheight = pagesize[0], pagesize[1]
            imgwidthpdf, imgheightpdf = fitfun(
                fit,
                px_to_pt(imgwidthpx, ndpi[0]),
                px_to_pt(imgheightpx, ndpi[1]),
                scale_imgsize(imgsize[0], imgwidthpx, ndpi[0]),
                scale_imgsize(imgsize[1], imgheightpx, ndpi[1]),
            )
            return pagewidth, pageheight, imgwidthpdf, imgheightpdf

        return layout_fun
    raise NotImplementedError


def default_layout_fun(imgwidthpx, imgheightpx, ndpi):
    imgwidthpdf = pagewidth = px_to_pt(imgwidthpx, ndpi[0])
    imgheightpdf = pageheight = px_to_pt(imgheightpx, ndpi[1])
    return pagewidth, pageheight, imgwidthpdf, imgheightpdf


def get_fixed_dpi_layout_fun(fixed_dpi):
    """Layout function that overrides whatever DPI is claimed in input images.

    >>> layout_fun = get_fixed_dpi_layout_fun((300, 300))
    >>> convert(image1, layout_fun=layout_fun, ... outputstream=...)
    """

    def fixed_dpi_layout_fun(imgwidthpx, imgheightpx, ndpi):
        return default_layout_fun(imgwidthpx, imgheightpx, fixed_dpi)

    return fixed_dpi_layout_fun


def find_scale(pagewidth, pageheight):
    """Find the power of 10 (10, 100, 1000...) that will reduce the scale
    below the PDF specification limit of 14400 PDF units (=200 inches)"""
    from math import log10, ceil

    major = max(pagewidth, pageheight)
    oversized = major / 14400.0

    return 10 ** ceil(log10(oversized))


# given one or more input image, depending on outputstream, either return a
# string containing the whole PDF if outputstream is None or write the PDF
# data to the given file-like object and return None
#
# Input images can be given as file like objects (they must implement read()),
# as a binary string representing the image content or as filenames to the
# images.
def convert(*images, **kwargs):

    _default_kwargs = dict(
        title=None,
        author=None,
        creator=None,
        producer=None,
        creationdate=None,
        moddate=None,
        subject=None,
        keywords=None,
        colorspace=None,
        nodate=False,
        layout_fun=default_layout_fun,
        viewer_panes=None,
        viewer_initial_page=None,
        viewer_magnification=None,
        viewer_page_layout=None,
        viewer_fit_window=False,
        viewer_center_window=False,
        viewer_fullscreen=False,
        with_pdfrw=False,
        outputstream=None,
        first_frame_only=False,
        allow_oversized=True,
        cropborder=None,
        bleedborder=None,
        trimborder=None,
        artborder=None,
    )
    for kwname, default in _default_kwargs.items():
        if kwname not in kwargs:
            kwargs[kwname] = default

    pdf = pdfdoc(
        "1.3",
        kwargs["title"],
        kwargs["author"],
        kwargs["creator"],
        kwargs["producer"],
        kwargs["creationdate"],
        kwargs["moddate"],
        kwargs["subject"],
        kwargs["keywords"],
        kwargs["nodate"],
        kwargs["viewer_panes"],
        kwargs["viewer_initial_page"],
        kwargs["viewer_magnification"],
        kwargs["viewer_page_layout"],
        kwargs["viewer_fit_window"],
        kwargs["viewer_center_window"],
        kwargs["viewer_fullscreen"],
        kwargs["with_pdfrw"],
    )

    # backwards compatibility with older img2pdf versions where the first
    # argument to the function had to be given as a list
    if len(images) == 1:
        # if only one argument was given and it is a list, expand it
        if isinstance(images[0], (list, tuple)):
            images = images[0]

    if not isinstance(images, (list, tuple)):
        images = [images]

    for img in images:
        # img is allowed to be a path, a binary string representing image data
        # or a file-like object (really anything that implements read())
        try:
            rawdata = img.read()
        except AttributeError:
            if not isinstance(img, (str, bytes)):
                raise TypeError("Neither implements read() nor is str or bytes")
            # the thing doesn't have a read() function, so try if we can treat
            # it as a file name
            try:
                f = open(img, "rb")
            except Exception:
                # whatever the exception is (string could contain NUL
                # characters or the path could just not exist) it's not a file
                # name so we now try treating it as raw image content
                rawdata = img
            else:
                # we are not using a "with" block here because we only want to
                # catch exceptions thrown by open(). The read() may throw its
                # own exceptions like MemoryError which should be handled
                # differently.
                rawdata = f.read()
                f.close()

        for (
            color,
            ndpi,
            imgformat,
            imgdata,
            imgwidthpx,
            imgheightpx,
            palette,
            inverted,
            depth,
            rotation,
        ) in read_images(rawdata, kwargs["colorspace"], kwargs["first_frame_only"]):
            pagewidth, pageheight, imgwidthpdf, imgheightpdf = kwargs["layout_fun"](
                imgwidthpx, imgheightpx, ndpi
            )

            userunit = None
            if pagewidth < 3.00 or pageheight < 3.00:
                logging.warning(
                    "pdf width or height is below 3.00 - too small for some viewers!"
                )
            elif pagewidth > 14400.0 or pageheight > 14400.0:
                if kwargs["allow_oversized"]:
                    userunit = find_scale(pagewidth, pageheight)
                    pagewidth /= userunit
                    pageheight /= userunit
                    imgwidthpdf /= userunit
                    imgheightpdf /= userunit
                else:
                    raise PdfTooLargeError(
                        "pdf width or height must not exceed 200 inches."
                    )
            # the image is always centered on the page
            imgxpdf = (pagewidth - imgwidthpdf) / 2.0
            imgypdf = (pageheight + imgheightpdf) / 2.0
            pdf.add_imagepage(
                color,
                imgwidthpx,
                imgheightpx,
                imgformat,
                imgdata,
                imgwidthpdf,
                imgheightpdf,
                imgxpdf,
                imgypdf,
                pagewidth,
                pageheight,
                userunit,
                palette,
                inverted,
                depth,
                rotation,
                kwargs["cropborder"],
                kwargs["bleedborder"],
                kwargs["trimborder"],
                kwargs["artborder"],
            )

    if kwargs["outputstream"]:
        pdf.tostream(kwargs["outputstream"])
        return

    return pdf.tostring()

def convert_ImageList(*images, **kwargs):

    _default_kwargs = dict(
        title=None,
        author=None,
        creator=None,
        producer=None,
        creationdate=None,
        moddate=None,
        subject=None,
        keywords=None,
        colorspace=None,
        nodate=False,
        layout_fun=default_layout_fun,
        viewer_panes=None,
        viewer_initial_page=None,
        viewer_magnification=None,
        viewer_page_layout=None,
        viewer_fit_window=False,
        viewer_center_window=False,
        viewer_fullscreen=False,
        with_pdfrw=False,
        outputstream=None,
        first_frame_only=False,
        allow_oversized=True,
        cropborder=None,
        bleedborder=None,
        trimborder=None,
        artborder=None,
    )
    for kwname, default in _default_kwargs.items():
        if kwname not in kwargs:
            kwargs[kwname] = default

    pdf = pdfdoc(
        "1.3",
        kwargs["title"],
        kwargs["author"],
        kwargs["creator"],
        kwargs["producer"],
        kwargs["creationdate"],
        kwargs["moddate"],
        kwargs["subject"],
        kwargs["keywords"],
        kwargs["nodate"],
        kwargs["viewer_panes"],
        kwargs["viewer_initial_page"],
        kwargs["viewer_magnification"],
        kwargs["viewer_page_layout"],
        kwargs["viewer_fit_window"],
        kwargs["viewer_center_window"],
        kwargs["viewer_fullscreen"],
        kwargs["with_pdfrw"],
    )

    # backwards compatibility with older img2pdf versions where the first
    # argument to the function had to be given as a list
    if len(images) == 1:
        # if only one argument was given and it is a list, expand it
        if isinstance(images[0], (list, tuple)):
            images = images[0]

    if not isinstance(images, (list, tuple)):
        images = [images]

    while (1):
        if (len(images) == 0):
            break
        image_item = images.pop(0)
        if (image_item == None):
            coordinates = images.pop(0)
            collected_images = images[:len(coordinates)]
            del images[:len(coordinates)]
            pdf.add_multi_imagepage(coordinates, collected_images)
            continue

        (
            color,
            ndpi,
            imgformat,
            imgdata,
            imgwidthpx,
            imgheightpx,
            palette,
            inverted,
            depth,
            rotation,
        ) = image_item

        pagewidth, pageheight, imgwidthpdf, imgheightpdf = kwargs["layout_fun"](
            imgwidthpx, imgheightpx, ndpi
        )
        if (pageheight < 0):
            pageheight = -pageheight

        userunit = None
        if pagewidth < 3.00 or pageheight < 3.00:
            logging.warning(
                "pdf width or height is below 3.00 - too small for some viewers!"
            )
        elif pagewidth > 14400.0 or pageheight > 14400.0:
            if kwargs["allow_oversized"]:
                userunit = find_scale(pagewidth, pageheight)
                pagewidth /= userunit
                pageheight /= userunit
                imgwidthpdf /= userunit
                imgheightpdf /= userunit
            else:
                raise PdfTooLargeError(
                    "pdf width or height must not exceed 200 inches."
                )
        # the image is always centered on the page
        imgxpdf = (pagewidth - imgwidthpdf) / 2.0
        imgypdf = (pageheight + imgheightpdf) / 2.0
        pdf.add_imagepage(
            color,
            imgwidthpx,
            imgheightpx,
            imgformat,
            imgdata,
            imgwidthpdf,
            imgheightpdf,
            imgxpdf,
            imgypdf,
            pagewidth,
            pageheight,
            userunit,
            palette,
            inverted,
            depth,
            rotation,
            kwargs["cropborder"],
            kwargs["bleedborder"],
            kwargs["trimborder"],
            kwargs["artborder"],
        )

    if kwargs["outputstream"]:
        pdf.tostream(kwargs["outputstream"])
        return

    return pdf.tostring()

def parse_num(num, name):
    if num == "":
        return None
    unit = None
    if num.endswith("pt"):
        unit = Unit.pt
    elif num.endswith("cm"):
        unit = Unit.cm
    elif num.endswith("mm"):
        unit = Unit.mm
    elif num.endswith("in"):
        unit = Unit.inch
    else:
        try:
            num = float(num)
        except ValueError:
            msg = (
                "%s is not a floating point number and doesn't have a "
                "valid unit: %s" % (name, num)
            )
            raise argparse.ArgumentTypeError(msg)
    if unit is None:
        unit = Unit.pt
    else:
        num = num[:-2]
        try:
            num = float(num)
        except ValueError:
            msg = "%s is not a floating point number: %s" % (name, num)
            raise argparse.ArgumentTypeError(msg)
    if unit == Unit.cm:
        num = cm_to_pt(num)
    elif unit == Unit.mm:
        num = mm_to_pt(num)
    elif unit == Unit.inch:
        num = in_to_pt(num)
    return num


def parse_imgsize_num(num, name):
    if num == "":
        return None
    unit = None
    if num.endswith("pt"):
        unit = ImgUnit.pt
    elif num.endswith("cm"):
        unit = ImgUnit.cm
    elif num.endswith("mm"):
        unit = ImgUnit.mm
    elif num.endswith("in"):
        unit = ImgUnit.inch
    elif num.endswith("dpi"):
        unit = ImgUnit.dpi
    elif num.endswith("%"):
        unit = ImgUnit.perc
    else:
        try:
            num = float(num)
        except ValueError:
            msg = (
                "%s is not a floating point number and doesn't have a "
                "valid unit: %s" % (name, num)
            )
            raise argparse.ArgumentTypeError(msg)
    if unit is None:
        unit = ImgUnit.pt
    else:
        # strip off unit from string
        if unit == ImgUnit.dpi:
            num = num[:-3]
        elif unit == ImgUnit.perc:
            num = num[:-1]
        else:
            num = num[:-2]
        try:
            num = float(num)
        except ValueError:
            msg = "%s is not a floating point number: %s" % (name, num)
            raise argparse.ArgumentTypeError(msg)
    if unit == ImgUnit.cm:
        num = (ImgSize.abs, cm_to_pt(num))
    elif unit == ImgUnit.mm:
        num = (ImgSize.abs, mm_to_pt(num))
    elif unit == ImgUnit.inch:
        num = (ImgSize.abs, in_to_pt(num))
    elif unit == ImgUnit.pt:
        num = (ImgSize.abs, num)
    elif unit == ImgUnit.dpi:
        num = (ImgSize.dpi, num)
    elif unit == ImgUnit.perc:
        num = (ImgSize.perc, num)
    return num


def parse_pagesize_rectarg(string):
    transposed = string.endswith("^T")
    if transposed:
        string = string[:-2]
    if papersizes.get(string.lower()):
        string = papersizes[string.lower()]
    if "x" not in string:
        # if there is no separating "x" in the string, then the string is
        # interpreted as the width
        w = parse_num(string, "width")
        h = None
    else:
        w, h = string.split("x", 1)
        w = parse_num(w, "width")
        h = parse_num(h, "height")
    if transposed:
        w, h = h, w
    if w is None and h is None:
        raise argparse.ArgumentTypeError("at least one dimension must be specified")
    return w, h


def parse_imgsize_rectarg(string):
    transposed = string.endswith("^T")
    if transposed:
        string = string[:-2]
    if papersizes.get(string.lower()):
        string = papersizes[string.lower()]
    if "x" not in string:
        # if there is no separating "x" in the string, then the string is
        # interpreted as the width
        w = parse_imgsize_num(string, "width")
        h = None
    else:
        w, h = string.split("x", 1)
        w = parse_imgsize_num(w, "width")
        h = parse_imgsize_num(h, "height")
    if transposed:
        w, h = h, w
    if w is None and h is None:
        raise argparse.ArgumentTypeError("at least one dimension must be specified")
    return w, h


def parse_colorspacearg(string):
    for c in Colorspace:
        if c.name == string:
            return c
    allowed = ", ".join([c.name for c in Colorspace])
    raise argparse.ArgumentTypeError(
        "Unsupported colorspace: %s. Must be one of: %s." % (string, allowed)
    )


def parse_borderarg(string):
    if ":" in string:
        h, v = string.split(":", 1)
        if h == "":
            raise argparse.ArgumentTypeError("missing value before colon")
        if v == "":
            raise argparse.ArgumentTypeError("missing value after colon")
    else:
        if string == "":
            raise argparse.ArgumentTypeError("border option cannot be empty")
        h, v = string, string
    h, v = parse_num(h, "left/right border"), parse_num(v, "top/bottom border")
    if h is None and v is None:
        raise argparse.ArgumentTypeError("missing value")
    return h, v


def input_images(path):
    if path == "-":
        # we slurp in all data from stdin because we need to seek in it later
        if PY3:
            result = sys.stdin.buffer.read()
        else:
            result = sys.stdin.read()
        if len(result) == 0:
            raise argparse.ArgumentTypeError('"%s" is empty' % path)
    else:
        if PY3:
            try:
                if os.path.getsize(path) == 0:
                    raise argparse.ArgumentTypeError('"%s" is empty' % path)
                # test-read a byte from it so that we can abort early in case
                # we cannot read data from the file
                with open(path, "rb") as im:
                    im.read(1)
            except IsADirectoryError:
                raise argparse.ArgumentTypeError('"%s" is a directory' % path)
            except PermissionError:
                raise argparse.ArgumentTypeError('"%s" permission denied' % path)
            except FileNotFoundError:
                raise argparse.ArgumentTypeError('"%s" does not exist' % path)
        else:
            try:
                if os.path.getsize(path) == 0:
                    raise argparse.ArgumentTypeError('"%s" is empty' % path)
                # test-read a byte from it so that we can abort early in case
                # we cannot read data from the file
                with open(path, "rb") as im:
                    im.read(1)
            except IOError as err:
                raise argparse.ArgumentTypeError(str(err))
            except OSError as err:
                raise argparse.ArgumentTypeError(str(err))
        result = path
    return result


def parse_fitarg(string):
    for m in FitMode:
        if m.name == string.lower():
            return m
    raise argparse.ArgumentTypeError("unknown fit mode: %s" % string)


def parse_panes(string):
    for m in PageMode:
        if m.name == string.lower():
            return m
    allowed = ", ".join([m.name for m in PageMode])
    raise argparse.ArgumentTypeError(
        "Unsupported page mode: %s. Must be one of: %s." % (string, allowed)
    )


def parse_magnification(string):
    for m in Magnification:
        if m.name == string.lower():
            return m
    try:
        return float(string)
    except ValueError:
        pass
    allowed = ", ".join([m.name for m in Magnification])
    raise argparse.ArgumentTypeError(
        "Unsupported magnification: %s. Must be "
        "a floating point number or one of: %s." % (string, allowed)
    )


def parse_layout(string):
    for l in PageLayout:
        if l.name == string.lower():
            return l
    allowed = ", ".join([l.name for l in PageLayout])
    raise argparse.ArgumentTypeError(
        "Unsupported page layout: %s. Must be one of: %s." % (string, allowed)
    )


def valid_date(string):
    # first try parsing in ISO8601 format
    try:
        return datetime.strptime(string, "%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M")
    except ValueError:
        pass
    try:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pass
    # then try dateutil
    try:
        from dateutil import parser
    except ImportError:
        pass
    else:
        try:
            return parser.parse(string)
        except TypeError:
            pass
    # as a last resort, try the local date utility
    try:
        import subprocess
    except ImportError:
        pass
    else:
        try:
            utime = subprocess.check_output(["date", "--date", string, "+%s"])
        except subprocess.CalledProcessError:
            pass
        else:
            return datetime.utcfromtimestamp(int(utime))
    raise argparse.ArgumentTypeError("cannot parse date: %s" % string)


def main(argv=sys.argv):
    rendered_papersizes = ""
    for k, v in sorted(papersizes.items()):
        rendered_papersizes += "    %-8s %s\n" % (papernames[k], v)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Losslessly convert raster images to PDF without re-encoding PNG, JPEG, and
JPEG2000 images. This leads to a lossless conversion of PNG, JPEG and JPEG2000
images with the only added file size coming from the PDF container itself.
Other raster graphics formats are losslessly stored using the same encoding
that PNG uses. Since PDF does not support images with transparency and since
img2pdf aims to never be lossy, input images with an alpha channel are not
supported.

The output is sent to standard output so that it can be redirected into a file
or to another program as part of a shell pipe. To directly write the output
into a file, use the -o or --output option.

Options:
""",
        epilog="""\
Colorspace:
  Currently, the colorspace must be forced for JPEG 2000 images that are not in
  the RGB colorspace.  Available colorspace options are based on Python Imaging
  Library (PIL) short handles.

    RGB      RGB color
    L        Grayscale
    1        Black and white (internally converted to grayscale)
    CMYK     CMYK color
    CMYK;I   CMYK color with inversion (for CMYK JPEG files from Adobe)

Paper sizes:
  You can specify the short hand paper size names shown in the first column in
  the table below as arguments to the --pagesize and --imgsize options.  The
  width and height they are mapping to is shown in the second column.  Giving
  the value in the second column has the same effect as giving the short hand
  in the first column. Appending ^T (a caret/circumflex followed by the letter
  T) turns the paper size from portrait into landscape. The postfix thus
  symbolizes the transpose. The values are case insensitive.

%s

Fit options:
  The img2pdf options for the --fit argument are shown in the first column in
  the table below. The function of these options can be mapped to the geometry
  operators of imagemagick. For users who are familiar with imagemagick, the
  corresponding operator is shown in the second column.  The third column shows
  whether or not the aspect ratio is preserved for that option (same as in
  imagemagick). Just like imagemagick, img2pdf tries hard to preserve the
  aspect ratio, so if the --fit argument is not given, then the default is
  "into" which corresponds to the absence of any operator in imagemagick.
  The value of the --fit option is case insensitive.

    into    |   | Y | The default. Width and height values specify maximum
            |   |   | values.
   ---------+---+---+----------------------------------------------------------
    fill    | ^ | Y | Width and height values specify the minimum values.
   ---------+---+---+----------------------------------------------------------
    exact   | ! | N | Width and height emphatically given.
   ---------+---+---+----------------------------------------------------------
    shrink  | > | Y | Shrinks an image with dimensions larger than the given
            |   |   | ones (and otherwise behaves like "into").
   ---------+---+---+----------------------------------------------------------
    enlarge | < | Y | Enlarges an image with dimensions smaller than the given
            |   |   | ones (and otherwise behaves like "into").

Argument parsing:
  Argument long options can be abbreviated to a prefix if the abbreviation is
  unambiguous. That is, the prefix must match a unique option.

  Beware of your shell interpreting argument values as special characters (like
  the semicolon in the CMYK;I colorspace option). If in doubt, put the argument
  values in single quotes.

  If you want an argument value to start with one or more minus characters, you
  must use the long option name and join them with an equal sign like so:

    $ img2pdf --author=--test--

  If your input file name starts with one or more minus characters, either
  separate the input files from the other arguments by two minus signs:

    $ img2pdf -- --my-file-starts-with-two-minuses.jpg

  Or be more explicit about its relative path by prepending a ./:

    $ img2pdf ./--my-file-starts-with-two-minuses.jpg

  The order of non-positional arguments (all arguments other than the input
  images) does not matter.

Examples:
  Lines starting with a dollar sign denote commands you can enter into your
  terminal. The dollar sign signifies your command prompt. It is not part of
  the command you type.

  Convert two scans in JPEG format to a PDF document.

    $ img2pdf --output out.pdf page1.jpg page2.jpg

  Convert a directory of JPEG images into a PDF with printable A4 pages in
  landscape mode. On each page, the photo takes the maximum amount of space
  while preserving its aspect ratio and a print border of 2 cm on the top and
  bottom and 2.5 cm on the left and right hand side.

    $ img2pdf --output out.pdf --pagesize A4^T --border 2cm:2.5cm *.jpg

  On each A4 page, fit images into a 10 cm times 15 cm rectangle but keep the
  original image size if the image is smaller than that.

    $ img2pdf --output out.pdf -S A4 --imgsize 10cmx15cm --fit shrink *.jpg

  Prepare a directory of photos to be printed borderless on photo paper with a
  3:2 aspect ratio and rotate each page so that its orientation is the same as
  the input image.

    $ img2pdf --output out.pdf --pagesize 15cmx10cm --auto-orient *.jpg

  Encode a grayscale JPEG2000 image. The colorspace has to be forced as img2pdf
  cannot read it from the JPEG2000 file automatically.

    $ img2pdf --output out.pdf --colorspace L input.jp2

Written by Johannes 'josch' Schauer <josch@mister-muffin.de>

Report bugs at https://gitlab.mister-muffin.de/josch/img2pdf/issues
"""
        % rendered_papersizes,
    )

    parser.add_argument(
        "images",
        metavar="infile",
        type=input_images,
        nargs="*",
        help="Specifies the input file(s) in any format that can be read by "
        "the Python Imaging Library (PIL). If no input images are given, then "
        'a single image is read from standard input. The special filename "-" '
        "can be used once to read an image from standard input. To read a "
        'file in the current directory with the filename "-", pass it to '
        'img2pdf by explicitly stating its relative path like "./-".',
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Makes the program operate in verbose mode, printing messages on "
        "standard error.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s " + __version__,
        help="Prints version information and exits.",
    )
    gui_group = parser.add_mutually_exclusive_group(required=False)
    gui_group.add_argument(
        "--gui",
        dest="gui",
        action="store_true",
        help="run tkinter gui (default on Windows)",
    )
    gui_group.add_argument(
        "--nogui",
        dest="gui",
        action="store_false",
        help="don't run tkinter gui (default elsewhere)",
    )
    if platform.system() == "Windows":
        parser.set_defaults(gui=True)
    else:
        parser.set_defaults(gui=False)

    outargs = parser.add_argument_group(
        title="General output arguments",
        description="Arguments controlling the output format.",
    )

    # In Python3 we have to output to sys.stdout.buffer because we write are
    # bytes and not strings. In certain situations, like when the main
    # function is wrapped by contextlib.redirect_stdout(), sys.stdout does not
    # have the buffer attribute. Thus we write to sys.stdout by default and
    # to sys.stdout.buffer if it exists.
    outargs.add_argument(
        "-o",
        "--output",
        metavar="out",
        type=argparse.FileType("wb"),
        default=sys.stdout.buffer if hasattr(sys.stdout, "buffer") else sys.stdout,
        help="Makes the program output to a file instead of standard output.",
    )
    outargs.add_argument(
        "-C",
        "--colorspace",
        metavar="colorspace",
        type=parse_colorspacearg,
        help="""
Forces the PIL colorspace. See the epilogue for a list of possible values.
Usually the PDF colorspace would be derived from the color space of the input
image. This option overwrites the automatically detected colorspace from the
input image and thus forces a certain colorspace in the output PDF /ColorSpace
property. This is useful for JPEG 2000 images with a different colorspace than
RGB.""",
    )

    outargs.add_argument(
        "-D",
        "--nodate",
        action="store_true",
        help="Suppresses timestamps in the output and thus makes the output "
        "deterministic between individual runs. You can also manually "
        "set a date using the --moddate and --creationdate options.",
    )

    outargs.add_argument(
        "--without-pdfrw",
        action="store_true",
        help="By default, img2pdf uses the pdfrw library to create the output "
        "PDF if pdfrw is available. If you want to use the internal PDF "
        "generator of img2pdf even if pdfrw is present, then pass this "
        "option. This can be useful if you want to have unicode metadata "
        "values which pdfrw does not yet support (See "
        "https://github.com/pmaupin/pdfrw/issues/39) or if you want the "
        "PDF code to be more human readable.",
    )

    outargs.add_argument(
        "--first-frame-only",
        action="store_true",
        help="By default, img2pdf will convert multi-frame images like "
        "multi-page TIFF or animated GIF images to one page per frame. "
        "This option will only let the first frame of every multi-frame "
        "input image be converted into a page in the resulting PDF.",
    )

    outargs.add_argument(
        "--pillow-limit-break",
        action="store_true",
        help="img2pdf uses the Python Imaging Library Pillow to read input "
        "images. Pillow limits the maximum input image size to %d pixels "
        "to prevent decompression bomb denial of service attacks. If "
        "your input image contains more pixels than that, use this "
        "option to disable this safety measure during this run of img2pdf"
        % Image.MAX_IMAGE_PIXELS,
    )

    sizeargs = parser.add_argument_group(
        title="Image and page size and layout arguments",
        description="""\
Every input image will be placed on its own page. The image size is controlled
by the dpi value of the input image or, if unset or missing, the default dpi of
%.2f. By default, each page will have the same size as the image it shows.
Thus, there will be no visible border between the image and the page border by
default. If image size and page size are made different from each other by the
options in this section, the image will always be centered in both dimensions.

The image size and page size can be explicitly set using the --imgsize and
--pagesize options, respectively.  If either dimension of the image size is
specified but the same dimension of the page size is not, then the latter will
be derived from the former using an optional minimal distance between the image
and the page border (given by the --border option) and/or a certain fitting
strategy (given by the --fit option). The converse happens if a dimension of
the page size is set but the same dimension of the image size is not.

Any length value in below options is represented by the meta variable L which
is a floating point value with an optional unit appended (without a space
between them). The default unit is pt (1/72 inch, the PDF unit) and other
allowed units are cm (centimeter), mm (millimeter), and in (inch).

Any size argument of the format LxL in the options below specifies the width
and height of a rectangle where the first L represents the width and the second
L represents the height with an optional unit following each value as described
above.  Either width or height may be omitted. If the height is omitted, the
separating x can be omitted as well. Omitting the width requires to prefix the
height with the separating x. The missing dimension will be chosen so to not
change the image aspect ratio. Instead of giving the width and height
explicitly, you may also specify some (case-insensitive) common page sizes such
as letter and A4.  See the epilogue at the bottom for a complete list of the
valid sizes.

The --fit option scales to fit the image into a rectangle that is either
derived from the --imgsize option or otherwise from the --pagesize option.
If the --border option is given in addition to the --imgsize option while the
--pagesize option is not given, then the page size will be calculated from the
image size, respecting the border setting. If the --border option is given in
addition to the --pagesize option while the --imgsize option is not given, then
the image size will be calculated from the page size, respecting the border
setting. If the --border option is given while both the --pagesize and
--imgsize options are passed, then the --border option will be ignored.

The --pagesize option or the --imgsize option with the --border option will
determine the MediaBox size of the resulting PDF document.
"""
        % default_dpi,
    )

    sizeargs.add_argument(
        "-S",
        "--pagesize",
        metavar="LxL",
        type=parse_pagesize_rectarg,
        help="""
Sets the size of the PDF pages. The short-option is the upper case S because
it is an mnemonic for being bigger than the image size.""",
    )

    sizeargs.add_argument(
        "-s",
        "--imgsize",
        metavar="LxL",
        type=parse_imgsize_rectarg,
        help="""
Sets the size of the images on the PDF pages.  In addition, the unit dpi is
allowed which will set the image size as a value of dots per inch.  Instead of
a unit, width and height values may also have a percentage sign appended,
indicating a resize of the image by that percentage. The short-option is the
lower case s because it is an mnemonic for being smaller than the page size.
""",
    )
    sizeargs.add_argument(
        "-b",
        "--border",
        metavar="L[:L]",
        type=parse_borderarg,
        help="""
Specifies the minimal distance between the image border and the PDF page
border.  This value Is overwritten by explicit values set by --pagesize or
--imgsize.  The value will be used when calculating page dimensions from the
image dimensions or the other way round. One, or two length values can be given
as an argument, separated by a colon. One value specifies the minimal border on
all four sides. Two values specify the minimal border on the top/bottom and
left/right, respectively. It is not possible to specify asymmetric borders
because images will always be centered on the page.
""",
    )
    sizeargs.add_argument(
        "-f",
        "--fit",
        metavar="FIT",
        type=parse_fitarg,
        default=FitMode.into,
        help="""

If --imgsize is given, fits the image using these dimensions. Otherwise, fit
the image into the dimensions given by --pagesize.  FIT is one of into, fill,
exact, shrink and enlarge. The default value is "into". See the epilogue at the
bottom for a description of the FIT options.

""",
    )
    sizeargs.add_argument(
        "-a",
        "--auto-orient",
        action="store_true",
        help="""
If both dimensions of the page are given via --pagesize, conditionally swaps
these dimensions such that the page orientation is the same as the orientation
of the input image. If the orientation of a page gets flipped, then so do the
values set via the --border option.
""",
    )
    sizeargs.add_argument(
        "--crop-border",
        metavar="L[:L]",
        type=parse_borderarg,
        help="""
Specifies the border between the CropBox and the MediaBox. One, or two length
values can be given as an argument, separated by a colon. One value specifies
the border on all four sides. Two values specify the border on the top/bottom
and left/right, respectively. It is not possible to specify asymmetric borders.
""",
    )
    sizeargs.add_argument(
        "--bleed-border",
        metavar="L[:L]",
        type=parse_borderarg,
        help="""
Specifies the border between the BleedBox and the MediaBox. One, or two length
values can be given as an argument, separated by a colon. One value specifies
the border on all four sides. Two values specify the border on the top/bottom
and left/right, respectively. It is not possible to specify asymmetric borders.
""",
    )
    sizeargs.add_argument(
        "--trim-border",
        metavar="L[:L]",
        type=parse_borderarg,
        help="""
Specifies the border between the TrimBox and the MediaBox. One, or two length
values can be given as an argument, separated by a colon. One value specifies
the border on all four sides. Two values specify the border on the top/bottom
and left/right, respectively. It is not possible to specify asymmetric borders.
""",
    )
    sizeargs.add_argument(
        "--art-border",
        metavar="L[:L]",
        type=parse_borderarg,
        help="""
Specifies the border between the ArtBox and the MediaBox. One, or two length
values can be given as an argument, separated by a colon. One value specifies
the border on all four sides. Two values specify the border on the top/bottom
and left/right, respectively. It is not possible to specify asymmetric borders.
""",
    )

    metaargs = parser.add_argument_group(
        title="Arguments setting metadata",
        description="Options handling embedded timestamps, title and author "
        "information.",
    )
    metaargs.add_argument(
        "--title", metavar="title", type=str, help="Sets the title metadata value"
    )
    metaargs.add_argument(
        "--author", metavar="author", type=str, help="Sets the author metadata value"
    )
    metaargs.add_argument(
        "--creator", metavar="creator", type=str, help="Sets the creator metadata value"
    )
    metaargs.add_argument(
        "--producer",
        metavar="producer",
        type=str,
        default="img2pdf " + __version__,
        help="Sets the producer metadata value "
        "(default is: img2pdf " + __version__ + ")",
    )
    metaargs.add_argument(
        "--creationdate",
        metavar="creationdate",
        type=valid_date,
        help="Sets the UTC creation date metadata value in YYYY-MM-DD or "
        "YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS format or any format "
        "understood by python dateutil module or any format understood "
        "by `date --date`",
    )
    metaargs.add_argument(
        "--moddate",
        metavar="moddate",
        type=valid_date,
        help="Sets the UTC modification date metadata value in YYYY-MM-DD "
        "or YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS format or any format "
        "understood by python dateutil module or any format understood "
        "by `date --date`",
    )
    metaargs.add_argument(
        "--subject", metavar="subject", type=str, help="Sets the subject metadata value"
    )
    metaargs.add_argument(
        "--keywords",
        metavar="kw",
        type=str,
        nargs="+",
        help="Sets the keywords metadata value (can be given multiple times)",
    )

    viewerargs = parser.add_argument_group(
        title="PDF viewer arguments",
        description="PDF files can specify how they are meant to be "
        "presented to the user by a PDF viewer",
    )

    viewerargs.add_argument(
        "--viewer-panes",
        metavar="PANES",
        type=parse_panes,
        help="Instruct the PDF viewer which side panes to show. Valid values "
        'are "outlines" and "thumbs". It is not possible to specify both '
        "at the same time.",
    )
    viewerargs.add_argument(
        "--viewer-initial-page",
        metavar="NUM",
        type=int,
        help="Instead of showing the first page, instruct the PDF viewer to "
        "show the given page instead. Page numbers start with 1.",
    )
    viewerargs.add_argument(
        "--viewer-magnification",
        metavar="MAG",
        type=parse_magnification,
        help="Instruct the PDF viewer to open the PDF with a certain zoom "
        "level. Valid values are either a floating point number giving "
        'the exact zoom level, "fit" (zoom to fit whole page), "fith" '
        '(zoom to fit page width) and "fitbh" (zoom to fit visible page '
        "width).",
    )
    viewerargs.add_argument(
        "--viewer-page-layout",
        metavar="LAYOUT",
        type=parse_layout,
        help="Instruct the PDF viewer how to arrange the pages on the screen. "
        'Valid values are "single" (display single pages), "onecolumn" '
        '(one continuous column), "twocolumnright" (two continuous '
        'columns with odd number pages on the right) and "twocolumnleft" '
        "(two continuous columns with odd numbered pages on the left)",
    )
    viewerargs.add_argument(
        "--viewer-fit-window",
        action="store_true",
        help="Instruct the PDF viewer to resize the window to fit the page size",
    )
    viewerargs.add_argument(
        "--viewer-center-window",
        action="store_true",
        help="Instruct the PDF viewer to center the PDF viewer window",
    )
    viewerargs.add_argument(
        "--viewer-fullscreen",
        action="store_true",
        help="Instruct the PDF viewer to open the PDF in fullscreen mode",
    )

    args = parser.parse_args(argv[1:])

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.pillow_limit_break:
        Image.MAX_IMAGE_PIXELS = None

    if args.gui:
        gui()
        sys.exit(0)

    layout_fun = get_layout_fun(
        args.pagesize, args.imgsize, args.border, args.fit, args.auto_orient
    )

    # if no positional arguments were supplied, read a single image from
    # standard input
    if len(args.images) == 0:
        logging.info("reading image from standard input")
        try:
            if PY3:
                args.images = [sys.stdin.buffer.read()]
            else:
                args.images = [sys.stdin.read()]
        except KeyboardInterrupt:
            exit(0)

    # with the number of pages being equal to the number of images, the
    # value passed to --viewer-initial-page must be between 1 and that number
    if args.viewer_initial_page is not None:
        if args.viewer_initial_page < 1:
            parser.print_usage(file=sys.stderr)
            logging.error(
                "%s: error: argument --viewer-initial-page: must be "
                "greater than zero" % parser.prog
            )
            exit(2)
        if args.viewer_initial_page > len(args.images):
            parser.print_usage(file=sys.stderr)
            logging.error(
                "%s: error: argument --viewer-initial-page: must be "
                "less than or equal to the total number of pages" % parser.prog
            )
            exit(2)

    try:
        convert(
            *args.images,
            title=args.title,
            author=args.author,
            creator=args.creator,
            producer=args.producer,
            creationdate=args.creationdate,
            moddate=args.moddate,
            subject=args.subject,
            keywords=args.keywords,
            colorspace=args.colorspace,
            nodate=args.nodate,
            layout_fun=layout_fun,
            viewer_panes=args.viewer_panes,
            viewer_initial_page=args.viewer_initial_page,
            viewer_magnification=args.viewer_magnification,
            viewer_page_layout=args.viewer_page_layout,
            viewer_fit_window=args.viewer_fit_window,
            viewer_center_window=args.viewer_center_window,
            viewer_fullscreen=args.viewer_fullscreen,
            with_pdfrw=False,
            outputstream=args.output,
            first_frame_only=args.first_frame_only,
            cropborder=args.crop_border,
            bleedborder=args.bleed_border,
            trimborder=args.trim_border,
            artborder=args.art_border,
        )
    except Exception as e:
        logging.error("error: " + str(e))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            import traceback

            traceback.print_exc(file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
