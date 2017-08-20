#!/usr/bin/env python3

from parser import CAJParser
from utils import add_outlines, complete_toc

if __name__ == "__main__":
    # caj = CAJParser("test.caj")
    # print(caj.page_num)
    # print(caj.toc_num)
    # caj.output_toc("toc.tmp")
    # caj.convert("output.pdf")

    toc = [
        {
            "title": "Outline 1",
            "page": 0,
            "level": 1
        },
        {
            "title": "Outline 1.1",
            "page": 2,
            "level": 2
        },
        {
            "title": "Outline 1.2",
            "page": 4,
            "level": 2
        },
        {
            "title": "Outline 1.2.1",
            "page": 6,
            "level": 3
        },
        {
            "title": "Outline 1.2.2",
            "page": 8,
            "level": 3
        },
        {
            "title": "Outline 2",
            "page": 10,
            "level": 1
        },
        {
            "title": "Outline 2.1",
            "page": 12,
            "level": 2
        },
        {
            "title": "Outline 2.1.1",
            "page": 14,
            "level": 3
        },
        {
            "title": "Outline 3",
            "page": 16,
            "level": 1
        },
        {
            "title": "Outline 3.1",
            "page": 18,
            "level": 2
        },
        {
            "title": "Outline 3.1.1",
            "page": 20,
            "level": 3
        },
        {
            "title": "Outline 3.1.2",
            "page": 22,
            "level": 3
        },
        {
            "title": "Outline 3.1.3",
            "page": 24,
            "level": 3
        }
    ]
    add_outlines(toc, "output.pdf", "ol.pdf")

