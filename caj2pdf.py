#!/usr/bin/env python3

from parser import CAJParser
from utils import add_outlines

if __name__ == "__main__":
    # caj = CAJParser("test.caj")
    # print(caj.page_num)
    # print(caj.toc_num)
    # caj.output_toc("toc.tmp")
    # caj.convert("output.pdf")

    toc = [
        {
            "title": "Outline 1",
            "page": 0
        },
        {
            "title": "Outline 2",
            "page": 2
        },
        {
            "title": "Outline 3",
            "page": 4
        }
    ]
    add_outlines(toc, "output.pdf", "ol.pdf")
