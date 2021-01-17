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
        self.stats = {}
        self.offset = 0
        def Text(self):
            try:
                self.characters.append(bytes([self.data[self.offset+5],self.data[self.offset+4]]).decode("gbk"))
            except UnicodeDecodeError:
                # HTL: When cut-and-paste on Linux, these transform to GB18030,
                # but I believe they are OCR artifacts. Where they occur,
                # 0xA38D 0xA38a (always together) are line-breaks, and 0xA389, 0xA3A0
                # are tabs and spaces.
                hash = {
                    0xA389 : "\t",
                    0xA38a : "\n",
                    0xA38D : "\r",
                    0xA3A0 : " ",
                    # # GB18030
                    #0xA389 : "",
                    #0xA38a : "",
                    #0xA38D : "",
                    #0xA3A0 : "",
                }
                code = self.data[self.offset+5] * 256 + self.data[self.offset+4]
                try:
                    #self.characters.append("<0x%04X>\n" % code)
                    self.characters.append(hash[code])
                except KeyError:
                    self.characters.append("<0x%04X>\n" % code)
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

        while (self.offset < self.data_length):
            (dispatch_code,) = struct.unpack("H", self.data[self.offset:self.offset+2])
            self.offset += 2
            if (dispatch_code in dispatch_keys):
                dispatch[dispatch_code](self)
            else:
                self.offset +=2
                if (dispatch_code in self.stats.keys()):
                    self.stats[dispatch_code] +=1
                else:
                    self.stats[dispatch_code] = 1

    @property
    def texts(self):
        text = ''.join(self.characters)
        text.replace('\x00', '')
        text.replace('\r', '')
        return text
