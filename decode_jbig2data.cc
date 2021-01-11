/*
  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  This is a small wrapper around libpoppler to provide a python
  interface to decode JBIG2 stream.

  To build:

      cc -Wall `pkg-config --cflags poppler` -fPIC -shared -o libjbig2codec.so decode_jbig2data.cc `pkg-config --libs poppler`
*/

#include "JBIG2Stream.h"

int decode_jbig2data(char*, int, char*, int, int, int, int);

extern "C" {
int decode_jbig2data_c(char* inbuf, int bufsize, char* outptr, int width, int height, int width_in_padded_4bytes, int width_in_padded_bytes)
{
  return decode_jbig2data(inbuf, bufsize, outptr, width, height, width_in_padded_4bytes, width_in_padded_bytes);
}
}

int decode_jbig2data(char* inbuf, int bufsize, char* outptr, int width, int height, int width_in_padded_4bytes, int width_in_padded_bytes)
{
  int v12;

  Object globals;
  MemStream *v10 = new MemStream(inbuf, 0, bufsize, Object(objNull));
  Stream *v11 = new JBIG2Stream(v10, Object(objNull), &globals);
  v11->reset(); // required
  if ( height > 0 )
  {
    v12 = 0;
    char* v13 = outptr + (height - 1) * width_in_padded_4bytes;
    do
    {
      ++v12;
      for (int i = 0; i < width_in_padded_bytes; i++)
        {
          *(v13 + i) = 0xFF & (v11->getChar() ^ 0xFF);
        }
      v13 -= width_in_padded_4bytes;
    }
    while ( v12 != height );
  }
  return 0;
}
