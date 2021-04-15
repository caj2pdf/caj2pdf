/*
  Copyright 2021 (c) Hin-Tak Leung <htl10@users.sourceforge.net>
  See The FreeType Project LICENSE for license terms.

  Decode-only part of JBigCodec. Drop-in compatible with LibReaderEx's.
*/

#include <cstdlib>
#include <cstring>
#include "JBigDecode.h"

void JBigCodec::ByteIn()
{
  unsigned int v3;
  unsigned int v1 = this->read_count;
  int v2 = 0;
  if ( v1 < this->inbuf_length )
  {
    v3 = *(this->inbuf + v1); // Needs to be unsigned!
    this->read_count = v1 + 1;
    v2 = v3 << 8;
  }
  this->C_register += v2;
  this->CT = 8;
}

/* size in number of ints! */
void* JBigCodec::ClearLine(char* dest, unsigned int size)
{
  return memset(dest, 0, 4 * size);
}

/* size in number of ints! */
void* JBigCodec::CopyLine(char* dest, char* src, unsigned int size)
{
  return memcpy(dest, src, 4 * size);
}

/* Table 24 on page 45 of ITU-T REC T-82 */

static int LSZ[256] = {
0x5a1d,
0x2586, 0x1114, 0x080b, 0x03d8, 0x01da, 0x00e5, 0x006f, 0x0036,
0x001a, 0x000d, 0x0006, 0x0003, 0x0001, 0x5a7f, 0x3f25, 0x2cf2,
0x207c, 0x17b9, 0x1182, 0x0cef, 0x09a1, 0x072f, 0x055c, 0x0406,
0x0303, 0x0240, 0x01b1, 0x0144, 0x00f5, 0x00b7, 0x008a, 0x0068,
0x004e, 0x003b, 0x002c, 0x5ae1, 0x484c, 0x3a0d, 0x2ef1, 0x261f,
0x1f33, 0x19a8, 0x1518, 0x1177, 0x0e74, 0x0bfb, 0x09f8, 0x0861,
0x0706, 0x05cd, 0x04de, 0x040f, 0x0363, 0x02d4, 0x025c, 0x01f8,

0x01a4, 0x0160, 0x0125, 0x00f6, 0x00cb, 0x00ab, 0x008f, 0x5b12,
0x4d04, 0x412c, 0x37d8, 0x2fe8, 0x293c, 0x2379, 0x1edf, 0x1aa9,
0x174e, 0x1424, 0x119c, 0x0f6b, 0x0d51, 0x0bb6, 0x0a40, 0x5832,
0x4d1c, 0x438e, 0x3bdd, 0x34ee, 0x2eae, 0x299a, 0x2516, 0x5570,
0x4ca9, 0x44d9, 0x3e22, 0x3824, 0x32b4, 0x2e17, 0x56a8, 0x4f46,
0x47e5, 0x41cf, 0x3c3d, 0x375e, 0x5231, 0x4c0f, 0x4639, 0x415e,
0x5627, 0x50e7, 0x4b85, 0x5597, 0x504f, 0x5a10, 0x5522, 0x59eb,
};

static int NLPS[256] = {
 1,
14, 16, 18, 20, 23, 25, 28, 30,
33, 35,  9, 10, 12, 15, 36, 38,
39, 40, 42, 43, 45, 46, 48, 49,
51, 52, 54, 56, 57, 59, 60, 62,
63, 32, 33, 37, 64, 65, 67, 68,
69, 70, 72, 73, 74, 75, 77, 78,
79, 48, 50, 50, 51, 52, 53, 54,

55, 56, 57, 58, 59, 61, 61, 65,
80, 81, 82, 83, 84, 86, 87, 87,
72, 72, 74, 74, 75, 77, 77, 80,
88, 89, 90, 91, 92, 93, 86, 88,
95, 96, 97, 99, 99, 93, 95, 101,
102, 103, 104,  99, 105, 106, 107, 103,
105, 108, 109, 110, 111, 110, 112, 112,
};

static int NMPS[256] = {
 1,
 2,  3,  4,  5,  6,  7,  8,  9,
10, 11, 12, 13, 13, 15, 16, 17,
18, 19, 20, 21, 22, 23, 24, 25,
26, 27, 28, 29, 30, 31, 32, 33,
34, 35,  9, 37, 38, 39, 40, 41,
42, 43, 44, 45, 46, 47, 48, 49,
50, 51, 52, 53, 54, 55, 56, 57,

 58,  59,  60,  61,  62,  63,  32,  65,
 66,  67,  68,  69,  70,  71,  72,  73,
 74,  75,  76,  77,  78,  79,  48,  81,
 82,  83,  84,  85,  86,  87,  71,  89,
 90,  91,  92,  93,  94,  86,  96,  97,
 98,  99, 100,  93, 102, 103, 104,  99,
106, 107, 103, 109, 107, 111, 109, 111,
};

static int SWITCH[256] = {
1,
0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 1, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 1, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0,

0, 0, 0, 0, 0, 0, 0, 1,
0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 1,
0, 0, 0, 0, 0, 0, 0, 1,
0, 0, 0, 0, 0, 0, 1, 0,
0, 0, 0, 0, 0, 0, 0, 0,
1, 0, 0, 0, 0, 1, 0, 1,
};

void JBigCodec::LpsExchange(int CX, unsigned int ST_CX, unsigned int LSZ_ST_CX)
{
  int v6;

  if ( A_interval < LSZ_ST_CX )
  {
    PIX = MPS[CX];
    ST[CX] = NMPS[ST_CX];
  }
  else
  {
    v6 = (MPS[CX] ^ 1)& 1; // 1 - MPS[CX]
    PIX = v6;
    ST[CX] = NLPS[ST_CX];
    if ( SWITCH[ST_CX] == 1 )
      MPS[CX] = v6;
  }
  C_register -= A_interval << 16;
  A_interval = LSZ_ST_CX;
}

void JBigCodec::MpsExchange(int CX, unsigned int ST_CX, unsigned int LSZ_ST_CX)
{
  int v6;

  if ( A_interval >= LSZ_ST_CX )
  {
    PIX = MPS[CX];
    ST[CX] = NMPS[ST_CX];
  }
  else
  {
    v6 = (MPS[CX] ^ 1) & 1;
    PIX = v6;
    ST[CX] = NLPS[ST_CX];
    if ( SWITCH[ST_CX] == 1 )
      MPS[CX] = v6;
  }
}

int JBigCodec::Decode1(int CX)
{
  A_interval -= LSZ[ST[CX]];
  if ( A_interval <= C_register >> 16 )
  {
    LpsExchange(CX, ST[CX], LSZ[ST[CX]]);
  }
  else
  {
    PIX = MPS[CX];                   // difference
    if ( A_interval > 0x7FFF )
      return PIX;
    MpsExchange(CX, ST[CX], LSZ[ST[CX]]);
  }
  this->RenormDe();
  return PIX;
}

int JBigCodec::Decode(char* inbuf, unsigned int size, unsigned int height, unsigned int bitwidth, unsigned int bitwidth_in_padded_bytes, char*outbuf)
{
  this->bitwidth = bitwidth;
  this->height = height;
  this->width_in_padded_bytes = bitwidth_in_padded_bytes;
  memset(outbuf, 0, height * bitwidth_in_padded_bytes);
  this->outptr = outbuf;
  this->InitDecode(inbuf, size);
  this->LowestDecode();
  return 0;
}

int JBigCodec::Decode(int CX)
{
  A_interval -= LSZ[ST[CX]];
  if ( A_interval <= C_register >> 16 )
  {
    LpsExchange(CX, ST[CX], LSZ[ST[CX]]);
    this->RenormDe();
  }
  else
    {
      if ( A_interval <= 0x7FFF )
        {
          MpsExchange(CX, ST[CX], LSZ[ST[CX]]);
          this->RenormDe();
        }
      else
        PIX = MPS[CX]; // difference
    }
  return PIX;
}

/* size in ints! */
void* JBigCodec::DupLine(char* buf, unsigned int dest_offset, unsigned int src_offset, unsigned int size)
{
  return memcpy(buf + dest_offset, buf + src_offset, 4 * size);
}

int JBigCodec::GetBit(int line_offset, int bit_offset)
{
  static const unsigned char bitmask[8] = { 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01 };

  if (bit_offset < 0 || bit_offset >= this->bitwidth || line_offset <0)
    return 0;

  if (line_offset >= this->height)
    line_offset = this->height -1;

  return (*(char *)(this->outptr
                    + this->width_in_padded_bytes * (this->height - line_offset - 1)
                    + bit_offset / 3) & bitmask[bit_offset & 7]) != 0;
}

int JBigCodec::GetCX(int a2, int a3)
{
  int v3;
  int v4;
  int v5;
  int v6;
  int v7;

  v3 = a3;
  v4 = 2 * GetBit(a2 - 1, a3 + 2);
  v5 = 2 * (GetBit(a2 - 1, v3 + 1) + v4);
  v6 = 8 * (GetBit(a2 - 1, v3) + v5);
  v7 = 2 * (GetBit(a2 - 2, v3 + 1) + v6);
  return 2 * (GetBit(a2 - 2, v3) + v7);
}

void JBigCodec::InitDecode(char* inbuf, unsigned int buflen)
{
  this->inbuf_length = buflen;
  this->read_count = 0;
  this->inbuf = (unsigned char*)inbuf;
  memset((void *)this->MPS,   0, 0x4000u);
  memset((void *)ST, 0, 0x4000u);
  this->ByteIn();
  this->C_register <<=8;
  this->ByteIn();
  this->C_register <<=8;
  this->ByteIn();
  this->A_interval = 0x10000;
}

int JBigCodec::LowestDecode()
{
  int v2 = this->width_in_padded_bytes;
  int v3 = v2 + 2;
  int v4 = 3 * (v2 + 2);
  int v5 = 2 * v2;
  char *v15 = (char *)malloc(24 * (v2 + 2));
  this->ClearLine(v15, 2 * v4);
  int v6 = this->height;
  if ( v6 )
  {
    char *v7 = v15 + 8 * v3;
    char *v8 = v15 + 16 * v3;
    int v9 = this->width_in_padded_bytes * (v6 - 1);
    int v10 = 0;
    char *v13;
    for ( char *i = v15; ; i = v13 )
    {
      if ( this->Decode(0x29c) )
      {
        this->MakeTypicalLine(v10);
        this->CopyLine(v8, v7, v5);
      }
      else
      {
        this->ClearLine(v8, v5);
        unsigned int v14 = this->GetCX(v10, 0);
        this->LowestDecodeLine(v9, v7, i, v14, v8);
      }
      ++v10;
      if ( v10 >= this->height )
        break;
      v9 -= this->width_in_padded_bytes;
      v13 = v7;
      v7 = v8;
      v8 = i;
    }
  }
  if ( v15 )
    free(v15);
  return 0;
}

int JBigCodec::LowestDecodeLine(unsigned int scanline_offset, char* a3, char* a4, unsigned int cx, char* a6)
{
  char *v7 = a3;
  char *v8 = a4;
  unsigned int v9 = cx;
  int v10 = 0;
  int v11;
  int result = 0;
  int v13;

  do
  {
    this->Decode1(v9);
    v13 = (v9 >> 1) & 0xFDFF;
    if ( (this->PIX & 0xFF) == 1 )
    {
      *(this->outptr + (v10 >> 3) + scanline_offset) |= 1 << (~(char)v10 & 7);
      v13 |= 0x200u;
      *(a6 + v10) = 1;
    }
    v11 = v13 | 4;
    if ( *(v8 + v10 + 2) != 1 )
      v11 &= 0xFFFBu;
    v9 = v11 | 0x80;
    if ( *(v7 + v10 + 3) != 1 )
      v9 &= 0xFF7Fu;
    ++v10;
  }
  while ( v10 < this->bitwidth );
  return result;
}

/* this routine copies one line from the bottom upwards */
void* JBigCodec::MakeTypicalLine(int number)
{
  if (number > 0)
    {
      int max = this->height - 1;
      if (number <= max)
        {
          return this->DupLine(this->outptr,
                        this->width_in_padded_bytes * (max-number),
                        this->width_in_padded_bytes * (max-number) + this->width_in_padded_bytes,
                        this->width_in_padded_bytes >> 2);       /* bytes / 4 */
        }
    }
  return NULL;
}

void JBigCodec::RenormDe()
{
  do
  {
    if ( !this->CT )
    {
      this->ByteIn();
    }
    this->A_interval *= 2;
    this->C_register *= 2;
    -- this->CT;
  }
  while ( this->A_interval <= 0x7FFF );
  if ( !this->CT )
    this->ByteIn();
  return;
}
