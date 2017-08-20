import os
import PyPDF2.pdf as PDF
from PyPDF2 import PdfFileWriter, PdfFileReader


def fnd(f, s, start=0):
    fsize = f.seek(0, os.SEEK_END)
    f.seek(0)
    bsize = 4096
    buffer = None
    if start > 0:
        f.seek(start)
    overlap = len(s) - 1
    while True:
        if overlap <= f.tell() < fsize:
            f.seek(f.tell() - overlap)
        buffer = f.read(bsize)
        if buffer:
            pos = buffer.find(s)
            if pos >= 0:
                return f.tell() - (len(buffer) - pos)
        else:
            return -1


def fnd_all(f, s):
    results = []
    last_addr = -len(s)
    while True:
        addr = fnd(f, s, start=last_addr + len(s))
        if addr != -1:
            results.append(addr)
            last_addr = addr
        else:
            return results


def make_dest(pdfw, pg):
    d = PDF.ArrayObject()
    d.append(pdfw.getPage(pg).indirectRef)
    d.append(PDF.NameObject("/XYZ"))
    d.append(PDF.NullObject())
    d.append(PDF.NullObject())
    d.append(PDF.NullObject())
    return d


def complete_toc(toc):
    # Parent
    for i, t in enumerate(toc):
        if t["level"] == 1:
            t["parent"] = 0
            continue
        j = i
        while True:
            j -= 1
            if toc[j]["level"] == t["level"] - 1:
                break
        t["parent"] = j + 1
    # Prev & Next
    for i, t in enumerate(toc):
        j = i
        k = i
        while True:
            j -= 1
            k += 1
            if "prev" not in t and j > -1:
                if toc[j]["level"] == t["level"]:
                    t["prev"] = j + 1
            if "next" not in t and k < len(toc):
                if toc[k]["level"] == t["level"]:
                    t["next"] = k + 1
            if j <= -1 and k >= len(toc):
                break
    # First & Last
    for i, t in enumerate(toc):
        if i < len(toc) - 1 and toc[i + 1]["level"] == t["level"] + 1:
            t["first"] = i + 2
            j = i
            while True:
                j += 1
                if j >= len(toc):
                    t["last"] = j
                    break
                if toc[j]["level"] != t["level"] + 1:
                    t["last"] = j
                    break


def add_outlines(toc, filename, output):
    complete_toc(toc)
    pdf_out = PdfFileWriter()
    pdf_in = PdfFileReader(open(filename, 'rb'))
    for p in pdf_in.pages:
        pdf_out.addPage(p)
    toc_num = len(toc)
    idoix = len(pdf_out._objects) + 1
    idorefs = [PDF.IndirectObject(x + idoix, 0, pdf_out) for x in range(toc_num + 1)]
    ol = PDF.DictionaryObject()
    ol.update({
        PDF.NameObject("/Type"): PDF.NameObject("/Outlines"),
        PDF.NameObject("/First"): idorefs[1],
        PDF.NameObject("/Last"): idorefs[-1],
        PDF.NameObject("/Count"): PDF.NumberObject(toc_num)
    })
    olitems = []
    for t in toc:
        oli = PDF.DictionaryObject()
        oli.update({
            PDF.NameObject("/Title"): PDF.TextStringObject(t["title"]),
            PDF.NameObject("/Parent"): idorefs[t["parent"]],
            PDF.NameObject("/Dest"): make_dest(pdf_out, t["page"])
        })
        olitems.append(oli)
    for ix, olitem in enumerate(olitems[:-1]):
        olitem.update({
            PDF.NameObject("/Next"): idorefs[ix + 2]
        })
    for ix, olitem in enumerate(olitems[1:]):
        olitem.update({
            PDF.NameObject("/Prev"): idorefs[ix + 1]
        })
    pdf_out._addObject(ol)
    for i in olitems:
        pdf_out._addObject(i)
    pdf_out._root_object.update({
        PDF.NameObject("/Outlines"): idorefs[0]
    })
    outputFile = open(output, "wb")
    pdf_out.write(outputFile)
    outputFile.close()
