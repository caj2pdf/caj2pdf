/*
  Copyright 2020-2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  This short program decodes the image data in a CAJ file.

  To build, copy "libreaderex_x64.so" from the Ubuntu AppImage
  to the current directory.
  (See "Analysing libreaderex" in the Wiki on how to)

  Then, run

      cc -DHAVE_MAIN -Wall -o jbigdec jbigdec.cc -Wl,-rpath,. -L. -lreaderex_x64

  For the python module, also:

      cc -Wall -fPIC --shared -o libjbigdec.so jbigdec.cc JBigDecode.cc

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
#include <cstring>

extern "C" {
  class JBigCodec {
  public:
    void ByteIn();
    void ClearLine(char*, unsigned int);
    void CopyLine(char*, char*, unsigned int);
    int Decode1(int);
    void Decode(char* inbuf, unsigned int size, unsigned int height, unsigned int bitwidth, unsigned int bitwidth_in_bytes /* rounded up to x4 */, char*outbuf);
    int Decode(int);
    void DupLine(char*, unsigned int, unsigned int, unsigned int);
    int GetBit(int, int);
    unsigned int GetCX(int, int);
    void InitDecode(char*, unsigned int);
    void LowestDecode();
    int LowestDecodeLine(unsigned int, char*, char*, unsigned int, char*);
    void MakeTypicalLine(int);
    void RenormDe();
  };
#ifdef HAVE_MAIN
  class CImage {
  public:
    static CImage* DecodeJbig(void*, unsigned int, unsigned int*);
    static CImage* DecodeJbig2(void*, unsigned int, unsigned int*);
    int SaveAsBmp(char const*);
  };

void SaveJbigAsBmp(void* in, unsigned int len, char const* outfile)
{
  CImage* x = CImage::DecodeJbig(in, len, NULL);
  x->SaveAsBmp(outfile);
}

void SaveJbig2AsBmp(void* in, unsigned int len, char const* outfile)
{
  CImage* x = CImage::DecodeJbig2(in, len, NULL);
  x->SaveAsBmp(outfile);
}
#endif

void jbigDecode(char* inbuf, unsigned int size, unsigned int height,
                unsigned int bitwidth, unsigned int bitwidth_in_bytes /* rounded up to x4 */, char*outbuf)
{
  JBigCodec *jbig = (JBigCodec *)calloc(0x8040, 1); // 0x8040 is linux 64-bit specific
  jbig->Decode(inbuf, size, height, bitwidth, bitwidth_in_bytes, outbuf);
  free(jbig);
}

}

#ifdef HAVE_MAIN
int main(int argc, char *argv[])
{
  size_t buflen = 80000; // large number - should be large enough to hold the whole input file.
  char *in = (char *)calloc(buflen, 1);

  FILE *fin = fopen(argv[1], "rb");

  size_t len = fread(in, 1, buflen, fin);

  unsigned int intout = 0;
  CImage* x = CImage::DecodeJbig(in, len, &intout);
  x->SaveAsBmp(argv[2]);

  int width  = in[4] | (in[5] << 8) | (in[6]  << 16) | (in[7]  << 24);
  int height = in[8] | (in[9] << 8) | (in[10] << 16) | (in[11] << 24);
  int bits_per_pixel = in[14] | (in[15] << 8);
  // padding to multiple of 4 bytes.
  int bytes_per_line = ((width * bits_per_pixel + 31) >> 5) << 2;

  char *out = (char *)calloc(height * bytes_per_line, 1);

  JBigCodec *jbig = (JBigCodec *)calloc(0x8040, 1); // 0x8040 is linux 64-bit specific
  jbig->Decode(in+48, len-48, height, width, bytes_per_line, out);
  free(jbig);

  FILE *fout = fopen("test.pbm", "wb");
  fprintf(fout, "P4\n");
  // PBM is padded to 8 rather than 32.
  // If the padding is larger, write padded file.
  if (bytes_per_line > ((width +7) >> 3))
    width = bytes_per_line << 3;
  fprintf(fout, "%d %d\n", width, height);
  fwrite(out, 1, bytes_per_line * height, fout);
  fclose(fout); // "cmp -i 62:13 x.bmp x.pbm" shows nothing - identical.
}
#endif
