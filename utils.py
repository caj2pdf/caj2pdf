import os
import sys
import PyPDF2.generic as PDF
from PyPDF2 import PdfFileWriter, PdfFileReader


class Node(object):
    def __init__(self, data, parent=None, lchild=None, rchild=None):
        self.data = data
        self.parent = parent
        self.lchild = lchild
        self.rchild = rchild

    @property
    def level(self):
        return self.data["level"]

    @property
    def index(self):
        return self.data["index"]

    def real_parent(self):
        p = self
        while True:
            c = p
            p = p.parent
            if p.lchild == c:
                return p
            if p.parent is None:
                return None

    def prev(self):
        if self.parent.rchild == self:
            return self.parent
        else:
            return None

    def next(self):
        return self.rchild

    def first(self):
        return self.lchild

    def last(self):
        f = self.first()
        if f is None:
            return None
        r = f
        while r.rchild is not None:
            r = r.rchild
        return r


class BTree(object):
    def __init__(self):
        self.root = Node({"level": 0, "index": 0}, None)
        self.cursor = self.root

    @property
    def current_level(self):
        return self.cursor.level

    def insert_as_lchild(self, node):
        self.cursor.lchild = node
        node.parent = self.cursor
        self.cursor = node

    def insert_as_rchild(self, node):
        self.cursor.rchild = node
        node.parent = self.cursor
        self.cursor = node


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


def fnd_rvrs(f, s, end=sys.maxsize):
    # find target in reverse direction
    fsize = f.seek(0, os.SEEK_END)
    bsize = 4096
    if len(s) > end:
        raise SystemExit("Too large string size for search.")
    f.seek(fsize - bsize)
    buffer = None
    size = bsize
    if bsize <= end < fsize:
        f.seek(end - bsize)
    elif 0 < end < bsize:
        size = end
        f.seek(0)
    overlap = len(s) - 1
    s = s[::-1]
    while True:
        buffer = f.read(size)
        if buffer:
            buffer = buffer[::-1]
            pos = buffer.find(s)
            if pos >= 0:
                return f.tell() - pos
        if (2 * bsize - overlap) < f.tell():
            f.seek(f.tell() - (2 * bsize - overlap))
            size = bsize
        elif (bsize - overlap) < f.tell():
            size = f.tell() - (bsize - overlap)
            f.seek(0)
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


def fnd_unuse_no(nos1, nos2):
    unuse_no = -1
    for i in range(99999):
        if (99999 - i not in nos1) and (99999 - i not in nos2):
            unuse_no = 99999 - i
            break
    if unuse_no == -1:
        raise SystemExit("Error on PDF objects numbering.")
    return unuse_no


def make_dest(pdfw, pg):
    d = PDF.ArrayObject()
    d.append(pdfw.getPage(pg).indirect_ref)
    d.append(PDF.NameObject("/XYZ"))
    d.append(PDF.NullObject())
    d.append(PDF.NullObject())
    d.append(PDF.NullObject())
    return d


def build_outlines_btree(toc):
    tree = BTree()
    for i, t in enumerate(toc):
        t["page"] -= 1  # Page starts at 0.
        t["index"] = i + 1
        node = Node(t)
        if t["level"] > tree.current_level:
            tree.insert_as_lchild(node)
        elif t["level"] == tree.current_level:
            tree.insert_as_rchild(node)
        else:
            while True:
                p = tree.cursor.real_parent()
                tree.cursor = p
                if p.level == t["level"]:
                    tree.insert_as_rchild(node)
                    break
        t["node"] = node


def add_outlines(toc, filename, output):
    build_outlines_btree(toc)
    pdf_out = PdfFileWriter()
    inputFile = open(filename, 'rb')
    pdf_in = PdfFileReader(inputFile)
    for p in pdf_in.pages:
        pdf_out.addPage(p)
    toc_num = len(toc)
    if (toc_num == 0): # Just copy if toc empty
        outputFile = open(output, "wb")
        pdf_out.write(outputFile)
        inputFile.close()
        outputFile.close()
        return
    idoix = len(pdf_out._objects) + 1
    idorefs = [PDF.IndirectObject(x + idoix, 0, pdf_out)
               for x in range(toc_num + 1)]
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
            PDF.NameObject("/Title"): PDF.TextStringObject(t["title"].decode("utf-8")),
            PDF.NameObject("/Dest"): make_dest(pdf_out, t["page"])
        })
        opt_keys = {"real_parent": "/Parent", "prev": "/Prev",
                    "next": "/Next", "first": "/First", "last": "/Last"}
        for k, v in opt_keys.items():
            n = getattr(t["node"], k)()
            if n is not None:
                oli.update({
                    PDF.NameObject(v): idorefs[n.index]
                })
        olitems.append(oli)
    pdf_out._add_object(ol)
    for i in olitems:
        pdf_out._add_object(i)
    pdf_out._root_object.update({
        PDF.NameObject("/Outlines"): idorefs[0]
    })
    outputFile = open(output, "wb")
    pdf_out.write(outputFile)
    inputFile.close()
    outputFile.close()
