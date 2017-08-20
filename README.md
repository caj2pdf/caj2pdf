# caj2pdf

## Why

[中国知网](http://cnki.net/)的某些文献（多为学位论文）仅提供其专有的 CAJ 格式下载，仅能使用知网提供的软件（如 [CAJViewer](http://cajviewer.cnki.net/) 等）打开，给文献的阅读和管理带来了不便（尤其是在非 Windows 系统上）。

若要将 CAJ 文件转换为 PDF 文件，可以通过 CAJViewer 的打印功能完成。但这样得到的 PDF 文件的内容为图片，无法进行文字的选择，且原文献的大纲列表也会丢失。本项目希望可以解决上述两问题。

## How far we've come

知网下载到的后缀为 `caj` 的文件内部结构其实分为两类：CAJ 格式和 HN 格式（受考察样本所限可能还有更多）。目前本项目支持 CAJ 格式文件的转换（并且受考察样本所限可能还有 Bug），HN 格式仅支持基本文件信息和大纲信息的读取，但在文件内容结构的分析上也取得了一些微小的进展。

**关于两种格式文件结构的分析进展和本项目的实现细节，请查阅项目 Wiki。**

## How to use

### 环境和依赖

- Python 3
- [PyPDF2](https://github.com/mstamy2/PyPDF2)
- [mutool](https://mupdf.com/index.html)

### 用法

```
# 打印文件基本信息（文件类型、页面数、大纲项目数）
caj2pdf show [input_file]
# 转换文件
caj2pdf convert [input_file] -o/--output [output_file]
# 从 CAJ 文件中提取大纲信息并添加至 PDF 文件
## 遇到不支持的文件类型或 Bug 时，可用 CAJViewer 打印 PDF 文件，并用这条命令为其添加大纲
caj2pdf outlines [input_file] -o/--output [pdf_file]
```

### 例

```
caj2pdf show test.caj
caj2pdf convert test.caj -o output.pdf
caj2pdf outlines test.caj -o printed.pdf
```

