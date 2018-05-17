#!/usr/bin/env python3

import os
import argparse
from cajparser import CAJParser
from utils import add_outlines

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="commands", dest="command")

    show_parser = subparsers.add_parser("show", help="Show the information of the CAJ file.")
    show_parser.add_argument("input", help="Path to the CAJ file.")

    convert_parser = subparsers.add_parser("convert", help="Convert the CAJ file to PDF file.")
    convert_parser.add_argument("input", help="Path to the CAJ file.")
    convert_parser.add_argument("-o", "--output", help="Output path to the PDF file.", required=True)

    outlines_parser = subparsers.add_parser("outlines", help="Extract outlines from the CAJ file and add it to PDF file.")
    outlines_parser.add_argument("input", help="Path to the CAJ file.")
    outlines_parser.add_argument("-o", "--output", help="Path to the PDF file.", required=True)

    args = parser.parse_args()

    if args.command == "show":
        caj = CAJParser(args.input)
        print("File: {0}\nType: {1}\nPage count: {2}\nOutlines count: {3}\n".format(
            args.input,
            caj.format,
            caj.page_num,
            caj.toc_num
        ))

    if args.command == "convert":
        caj = CAJParser(args.input)
        caj.convert(args.output)

    if args.command == "outlines":
        caj = CAJParser(args.input)
        toc = caj.get_toc()
        add_outlines(toc, args.output, "tmp.pdf")
        os.replace("tmp.pdf", args.output)
