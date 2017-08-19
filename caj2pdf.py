#!/usr/bin/env python3

from parser import CAJParser

if __name__ == "__main__":
    caj = CAJParser("test.caj")
    print(caj.page_num)
    print(caj.toc_num)
