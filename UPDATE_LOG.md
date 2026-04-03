# 更新日志 (Update Log)

## 2026-04-03 修复

### 1. 修复标准 C8 格式 (STD C8) 转换崩溃

**问题描述：**
- 标准 C8 格式（版本标识 `02 00 00 00`）转换时发生崩溃
- 错误信息：`ValueError: Image dimensions too large: 32797x311721985`

**原因分析：**
- 标准 C8 格式的图像数据嵌入在文本数据流中，不是独立存储
- 图像头中 `size_of_image_data = 0` 表示无独立图像数据
- 原代码尝试读取下一页的文本数据作为图像，导致 JBIG 解码失败

**修复方案：**
- 检测到 `size_of_image_data = 0` 时跳过图像处理
- 添加警告信息，说明标准 C8 格式的限制

**已知限制：**
- 标准 C8 格式的文本解析暂不支持，生成空白 PDF
- 需要进一步逆向工程来解析其专有文本编码格式

### 2. 添加 PyMuPDF 支持替代 mutool

**问题描述：**
- 原代码依赖 `mutool` 命令行工具修复 PDF xref 表
- 未安装 mutool 时转换失败，或生成有格式错误的 PDF

**修复方案：**
- 优先使用 PyMuPDF（Python 库）修复 PDF
- 如果没有 PyMuPDF，回退到 mutool
- 如果都不可用，生成未清理的 PDF 并显示安装提示

**安装方法：**
```bash
pip install PyMuPDF
# 或
pip install -r requirements.txt
```

### 3. 文件修改清单

| 文件 | 修改内容 |
|------|---------|
| `cajparser.py` | 修复 STD C8 图像处理逻辑；添加 PyMuPDF 支持 |
| `requirements.txt` | 添加 `PyMuPDF>=1.20.0` 依赖 |

### 4. 测试结果

| 文件格式 | 转换状态 | 备注 |
|---------|---------|------|
| HZ C8 (新版) | ✓ 成功 | 完全支持 |
| STD C8 (标准) | ✓ 成功 | 生成空白 PDF（文本解析不支持） |
| CAJ | ✓ 成功 | 需要 PyMuPDF 修复 xref 表 |
| HN | ✓ 成功 | 未修改，正常工作 |
| KDH | ✓ 成功 | 未修改，正常工作 |

### 5. 给原作者的说明

**英文版本（推荐用于 Issue/PR）：**

---

**Title:** Fix for Standard C8 format crash and mutool dependency

**Summary:**

This PR fixes two issues:

1. **Standard C8 format (version marker `02 00 00 00`) crash fix**
   - The STD C8 format stores image data embedded in text stream, not as separate blocks
   - When `size_of_image_data = 0`, the code incorrectly tried to read next page's text as image
   - Fix: Skip image processing when size is 0, with a warning message
   - Note: STD C8 text parsing is not yet supported (generates blank PDF)

2. **Replace mutool dependency with PyMuPDF**
   - Original code required `mutool` command-line tool for PDF xref repair
   - Now uses PyMuPDF (Python library) as primary method, with mutool as fallback
   - Updated `requirements.txt` to include `PyMuPDF>=1.20.0`

**Installation:**
```bash
pip install PyMuPDF
# or
pip install -r requirements.txt
```

**Test Results:**
- HZ C8: ✓ Works
- STD C8: ✓ Converts (blank PDF, text parsing not supported)
- CAJ: ✓ Works (requires PyMuPDF)
- HN/KDH: ✓ Works (unchanged)

---

**中文版本：**

---

**标题：** 修复标准 C8 格式崩溃和 mutool 依赖问题

**摘要：**

本次更新修复了两个问题：

1. **标准 C8 格式（版本标识 `02 00 00 00`）崩溃修复**
   - 标准 C8 格式的图像数据嵌入在文本流中，不是独立存储
   - 当 `size_of_image_data = 0` 时，原代码错误地读取下一页文本作为图像
   - 修复：检测到 size=0 时跳过图像处理，并显示警告
   - 注意：标准 C8 文本解析暂不支持（生成空白 PDF）

2. **使用 PyMuPDF 替代 mutool 依赖**
   - 原代码需要 `mutool` 命令行工具修复 PDF xref 表
   - 现在优先使用 PyMuPDF（Python 库），mutool 作为备选
   - 更新 `requirements.txt` 添加 `PyMuPDF>=1.20.0`

**安装方法：**
```bash
pip install PyMuPDF
# 或
pip install -r requirements.txt
```

**测试结果：**
- HZ C8: ✓ 正常
- STD C8: ✓ 可转换（空白 PDF，文本解析不支持）
- CAJ: ✓ 正常（需要 PyMuPDF）
- HN/KDH: ✓ 正常（未修改）

---
