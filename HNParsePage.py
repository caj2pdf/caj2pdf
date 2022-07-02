#  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
#  See The FreeType Project LICENSE for license terms.
#
#  HNParsePage class, for extracting text and image positions
import struct

class HNParsePage(object):
    def __init__(self, data, old_style=False):
        self.data = data
        self.data_length = len(data)
        self.characters = []
        self.figures = []
        self.stats = {}
        self.offset = 0
        def Text(self, code):
            try:
                self.characters.append(bytes([self.data[self.offset+5],self.data[self.offset+4]]).decode("gbk"))
            except IndexError: # short data, nothing to do
                pass
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

        def TextMulti(self, code):
            self.offset += 2
            if (code == 0x8001):
                self.characters.append("\n")
            while (1):
                if (self.data[self.offset+1] == 0x80):
                    break
                try:
                    self.characters.append(bytes([self.data[self.offset+3],self.data[self.offset+2]]).decode("gbk"))
                except UnicodeDecodeError:
                    self.characters.append("<0x%04X>\n" % (self.data[self.offset+3] * 256 + self.data[self.offset+2]))
                except IndexError: # short data, nothing to do
                    return
                self.offset += 4

        def Figure(self, code):
            try:
                self.data[self.offset+25]
            except IndexError: # short data, nothing to do
                return
            (ignore1, offset_x, offset_y, size_x, size_y, int2, int3, int4, int5)= struct.unpack("<HHHHHIIII", self.data[self.offset:self.offset+26])
            # in units of 1/2.473 pixels
            self.figures.append([offset_x, offset_y, size_x, size_y])
            self.offset += 26

        if (not old_style):
            dispatch = {
                0x8001 : Text,
                0x800A : Figure,
            }
        else:
            dispatch = {
                0x8001 : TextMulti,
                0x8070 : TextMulti,
                0x800A : Figure,
            }
        dispatch_keys = dispatch.keys()

        while (self.offset <= self.data_length - 2):
            (dispatch_code,) = struct.unpack("H", self.data[self.offset:self.offset+2])
            self.offset += 2
            if (dispatch_code in dispatch_keys):
                dispatch[dispatch_code](self, dispatch_code)
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
