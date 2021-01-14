#  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#  See The FreeType Project LICENSE for license terms.
#
#  HNParsePage class, for extracting text and image positions
import struct

class HNParsePage(object):
    def __init__(self, data):
        self.data = data
        self.data_length = len(data)
        self.characters = []
        self.figures = []
        self.offset = 0
        def Text(self):
            try:
                self.characters.append(bytes([self.data[self.offset+5],self.data[self.offset+4]]).decode("gbk"))
            except UnicodeDecodeError:
                code = self.data[self.offset+5] * 256 + self.data[self.offset+4]
                print("Undecoded:", code)
            self.offset += 6

        def Figure(self):
            (ignore1, offset_x, offset_y, size_x, size_y, int2, int3, int4, int5)= struct.unpack("<HHHHHIIII", self.data[self.offset:self.offset+26])
            # in units of 1/2.473 pixels
            self.figures.append([offset_x, offset_y, size_x, size_y])
            self.offset += 26

        dispatch = {
            0x8001 : Text,
            0x800A : Figure,
        }
        dispatch_keys = dispatch.keys()
        stats = {}

        while (self.offset < self.data_length):
            (dispatch_code,) = struct.unpack("H", self.data[self.offset:self.offset+2])
            self.offset += 2
            if (dispatch_code in dispatch_keys):
                dispatch[dispatch_code](self)
            else:
                self.offset +=2
                if (dispatch_code in stats.keys()):
                    stats[dispatch_code] +=1
                else:
                    stats[dispatch_code] = 1

    @property
    def texts(self):
        text = ''.join(self.characters)
        text.replace('\x00', '')
        text.replace('\r', '')
        return text
