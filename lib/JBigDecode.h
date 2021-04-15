/*
  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  Decode-only part of JBigCodec. Drop-in compatible with LibReaderEx's.

  Note: MPS/ST are very wasteful, as only 1-bit is used, and
        array of length 0x20 (5 contexts) instead of 0x4000 (14 contexts).

        GetBit() has /3 instead of >> 3, GetCX() only 5 contexts instead of 10/14.
        SLNTP / LNTP is neither the three-line template nor the two-line template
        form (and GetBit() is strange anyway).

        LpsExchange/MpsExchange/RenormDe/ByteIn/InitDecode are essentially
        identical as in T-82, as well as Decode1() and Decode().


*/
class JBigCodec {
public:
  void  ByteIn();
  void* ClearLine(char*, unsigned int);
  void* CopyLine(char*, char*, unsigned int);
  int   Decode1(int);
  int   Decode(char*, unsigned int, unsigned int, unsigned int, unsigned int, char*);
  int   Decode(int);
  void* DupLine(char*, unsigned int, unsigned int, unsigned int);
  int   GetBit(int, int);
  int   GetCX(int, int);
  void  InitDecode(char*, unsigned int);
  int   LowestDecode();
  int   LowestDecodeLine(unsigned int, char*, char*, unsigned int, char*);
  void  LpsExchange(int, unsigned int, unsigned int);
  void* MakeTypicalLine(int);
  void  MpsExchange(int, unsigned int, unsigned int);
  void  RenormDe();
private:
  unsigned int A_interval;
  int CT;
  int SC; /* Only used by Encode */
  unsigned int inbuf_length;
  int read_count;
  unsigned char *inbuf;
  unsigned int MPS[0x1000];
  unsigned int ST[0x1000];
  unsigned int C_register;
  int PIX;
  int BUFFER; /* Only used by Encode */
  int bitwidth;
  int height;
  int width_in_padded_bytes;
  char *outptr;
};
