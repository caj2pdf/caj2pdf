#!/usr/bin/env python3

#  Copyright 2020 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#  See The FreeType Project LICENSE for license terms.
#
#  python ctypes module and short program decodes the image data in a CAJ file.

#  To build, copy "libreaderex_x64.so" from the Ubuntu AppImage
#  to the current directory.
#  (See "Analysing libreaderex" in the Wiki on how to)
#
#  Then, run
#
#       cc -fPIC --shared -o libjbigdec.so -Wl,-rpath,. -Wall jbigdec.cc -L. -lreaderex_x64

from ctypes import *
import os

libjbigdec = cdll.LoadLibrary("./libjbigdec.so")

SaveJbigAsBmp = libjbigdec.SaveJbigAsBmp
SaveJbigAsBmp.restype = None
SaveJbigAsBmp.argtypes = [c_void_p, c_int, c_char_p]

SaveJbig2AsBmp = libjbigdec.SaveJbig2AsBmp
SaveJbig2AsBmp.restype = None
SaveJbig2AsBmp.argtypes = [c_void_p, c_int, c_char_p]

if __name__ == '__main__':
    import sys, os

    if len(sys.argv) < 3:
        print("Usage: %s input output" % sys.argv[0])
        sys.exit()

    f = open(sys.argv[1], "rb")
    buffer_size = os.stat(sys.argv[1]).st_size
    buffer = f.read()

    SaveJbigAsBmp(buffer, buffer_size, sys.argv[2].encode("ascii"))
