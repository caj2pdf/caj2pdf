#!/usr/bin/env python3

#  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#  See The FreeType Project LICENSE for license terms.
#
#  python ctypes module and short program to decode JBIG2 image data in a CAJ file.

#  To build, either libpoppler-based, or libjbig2dec-based (pick only one!):
#
#      cc -Wall `pkg-config --cflags poppler`  -fPIC -shared -o libjbig2codec.so decode_jbig2data.cc   `pkg-config --libs poppler`
#
#      cc -Wall `pkg-config --cflags jbig2dec` -fPIC -shared -o libjbig2codec.so decode_jbig2data_x.cc `pkg-config --libs jbig2dec`


from ctypes import *
import struct

import platform

arch = platform.architecture()
if (arch[1] == 'WindowsPE'):
    if (arch[0] == '64bit'):
        libjbig2codec = cdll.LoadLibrary("./lib/bin/libjbig2codec-w64.dll")
    else:
        libjbig2codec = cdll.LoadLibrary("./lib/bin/libjbig2codec-w32.dll")
else:
    libjbig2codec = cdll.LoadLibrary("./libjbig2codec.so")

decode_jbig2data_c    = libjbig2codec.decode_jbig2data_c

decode_jbig2data_c.restype   = c_int
decode_jbig2data_c.argtypes  = [c_void_p, c_int, c_void_p, c_int, c_int, c_int, c_int]

class CImage:
    def __init__(self, buffer):
        self.buffer = buffer
        self.buffer_size=len(buffer)
        (self.width, self.height,
         self.num_planes, self.bits_per_pixel) = struct.unpack("<IIHH", buffer[4:16])
        self.bytes_per_line = ((self.width * self.bits_per_pixel + 31) >> 5) << 2

    def DecodeJbig2(self):
        out = create_string_buffer(self.height * self.bytes_per_line)
        width_in_bytes = (self.width * self.bits_per_pixel + 7) >> 3
        decode_jbig2data_c(self.buffer[48:], self.buffer_size-48, out, self.width, self.height, self.bytes_per_line, width_in_bytes)
        return out

if __name__ == '__main__':
    import sys, os

    if len(sys.argv) < 3:
        print("Usage: %s input output" % sys.argv[0])
        sys.exit()

    f = open(sys.argv[1], "rb")
    buffer_size = os.stat(sys.argv[1]).st_size
    buffer = f.read()

    cimage = CImage(buffer)
    out = cimage.DecodeJbig2()

    # PBM is only padded to 8 rather than 32.
    # If the padding is larger, write padded file.
    width = cimage.width
    if (cimage.bytes_per_line > ((cimage.width +7) >> 3)):
        width = cimage.bytes_per_line << 3

    with open(sys.argv[2], "wb") as fout:
        fout.write("P4\n".encode("ascii"))
        fout.write(("%d %d\n" % (width, cimage.height)).encode("ascii"))
        fout.write(out)
