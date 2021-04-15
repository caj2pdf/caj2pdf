#!/usr/bin/env python3

#  Copyright 2020-2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#  See The FreeType Project LICENSE for license terms.
#
#  python ctypes module and short program decodes the image data in a CAJ file.

#  To build, copy "libreaderex_x64.so" from the Ubuntu AppImage
#  to the current directory.
#  (See "Analysing libreaderex" in the Wiki on how to)
#
#  Then, run
#
#       cc -Wall -fPIC --shared -o libjbigdec.so jbigdec.cc JBigDecode.cc

from ctypes import *
import os
import struct

import platform

arch = platform.architecture()
if (arch[1] == 'WindowsPE'):
    if (arch[0] == '64bit'):
        libjbigdec = cdll.LoadLibrary("./lib/bin/libjbigdec-w64.dll")
    else:
        libjbigdec = cdll.LoadLibrary("./lib/bin/libjbigdec-w32.dll")
else:
    libjbigdec = cdll.LoadLibrary("./libjbigdec.so")

#SaveJbigAsBmp = libjbigdec.SaveJbigAsBmp
#SaveJbigAsBmp.restype = None
#SaveJbigAsBmp.argtypes = [c_void_p, c_int, c_char_p]

#SaveJbig2AsBmp = libjbigdec.SaveJbig2AsBmp
#SaveJbig2AsBmp.restype = None
#SaveJbig2AsBmp.argtypes = [c_void_p, c_int, c_char_p]

jbigDecode = libjbigdec.jbigDecode
jbigDecode.restype = None
jbigDecode.argtypes = [c_void_p, c_int, c_int, c_int, c_int, c_void_p]

class CImage:
    def __init__(self, buffer):
        self.buffer = buffer
        self.buffer_size=len(buffer)
        (self.width, self.height,
         self.num_planes, self.bits_per_pixel) = struct.unpack("<IIHH", buffer[4:16])
        self.bytes_per_line = ((self.width * self.bits_per_pixel + 31) >> 5) << 2

    def DecodeJbig(self):
        out = create_string_buffer(self.height * self.bytes_per_line)
        jbigDecode(self.buffer[48:], self.buffer_size-48, self.height, self.width, self.bytes_per_line, out)
        return out

if __name__ == '__main__':
    import sys, os

    if len(sys.argv) < 3:
        print("Usage: %s input output" % sys.argv[0])
        sys.exit()

    f = open(sys.argv[1], "rb")
    buffer_size = os.stat(sys.argv[1]).st_size
    buffer = f.read()

    #SaveJbigAsBmp(buffer, buffer_size, sys.argv[2].encode("ascii"))

    cimage = CImage(buffer)
    out = cimage.DecodeJbig()

    # PBM is only padded to 8 rather than 32.
    # If the padding is larger, write padded file.
    width = cimage.width
    if (cimage.bytes_per_line > ((cimage.width +7) >> 3)):
        width = cimage.bytes_per_line << 3

    fout = open(sys.argv[2].replace(".bmp", ".pbm"), "wb")
    fout.write("P4\n".encode("ascii"))
    fout.write(("%d %d\n" % (width, cimage.height)).encode("ascii"))
    fout.write(out)
    fout.close()
