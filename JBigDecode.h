/*
  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  Decode-only part of JBigCodec. Drop-in compatible with LibReaderEx's.
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
  void LpsExchange(int, unsigned int, unsigned int);
  void* MakeTypicalLine(int);
  void MpsExchange(int, unsigned int, unsigned int);
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
