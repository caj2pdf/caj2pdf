/*
  Copyright 2020 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  This short program decodes the image data in a CAJ file.

  To build, copy "libreaderex_x64.so" from the Ubuntu AppImage
  to the current directory.
  (See "Analysing libreaderex" in the Wiki on how to)

  Then, run

      cc -o jbigdec -Wl,-rpath,. -Wall jbigdec.cc -L. -lreaderex_x64

  For the python module, also:

      cc -fPIC --shared -o libjbigdec.so -Wl,-rpath,. -Wall jbigdec.cc -L. -lreaderex_x64

  and to generate the "image_dump_*.dat":

      ./caj2pdf parse thesis.caj

  Identify which ones are DIB and which ones are JPG with:

      file image_dump_*.dat

  Usage example (Page 1 / Cover is likely JPG!):

      ./jbigdec image_dump_0002.dat page_0002.bmp
      ./jbigdec image_dump_0003.dat page_0003.bmp
      ...

  Note: The program outputs a few "string to int" while it is working.
        This is an anomaly with "libreaderex_x64.so".
*/

#include <cstdio>
#include <cstdlib>
#include <cctype>

extern "C" {
  class CImage {
  public:
    static CImage* DecodeJbig(void*, unsigned int, unsigned int*);
    int SaveAsBmp(char const*);
  };

void SaveJbigAsBmp(void* in, unsigned int len, char const* outfile)
{
  CImage* x = CImage::DecodeJbig(in, len, NULL);
  x->SaveAsBmp(outfile);
}

}

int main(int argc, char *argv[])
{
  size_t buflen = 80000; // large number - should be large enough to hold the whole input file.
  char *in = (char *)calloc(buflen, 1);

  FILE *fin = fopen(argv[1], "rb");

  size_t len = fread(in, 1, buflen, fin);

  unsigned int intout = 0;
  CImage* x = CImage::DecodeJbig(in, len, &intout);
  x->SaveAsBmp(argv[2]);
}
