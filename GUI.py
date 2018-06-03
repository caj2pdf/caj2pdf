from tkinter import *
import tkinter.filedialog
import os
import argparse
from cajparser import CAJParser
from utils import add_outlines
from tkinter import messagebox
global originpdf
global origincaj

originpdf=0
origincaj=0
def liulancajfunc():
	#print('1')
	global origincaj
	origincaj=tkinter.filedialog.askopenfilename(filetypes=[('CAJ','caj')])
	#print(origincaj[0:-3]+'pdf')
	caj.set(origincaj[-20:])
def liulanpdffunc():
	#print('2')
	global originpdf
	originpdf=tkinter.filedialog.askopenfilename(filetypes=[('PDF','pdf')])
	pdf.set(originpdf[-20:])
def zhuanhuanfunc():
	global originpdf
	global origincaj
	
	try:
		cajzh = CAJParser(origincaj)
		cajzh.convert(origincaj[0:-3]+'pdf') #暴力修改后缀为pdf
		messagebox.showinfo('提示','完成')
	except:
		messagebox.showinfo('错误','未知错误')
def addindex():
	global originpdf
	global origincaj
	try:
		cajadd = CAJParser(origincaj)
		toc = cajadd.get_toc()
		add_outlines(toc, originpdf, "tmp.pdf")
		os.replace("tmp.pdf", originpdf)
		messagebox.showinfo('提示','完成')
	except:
		messagebox.showinfo('错误','请检查是否选中caj或pdf')

root=Tk()
#root.maxsize(200,150)
#设置可变的标签内容
caj=StringVar()
caj.set('caj')
pdf=StringVar()
pdf.set('pdf')
#生成浏览标签及按钮
cajlb=Label(root,textvariable=caj).grid(row=0,column=0,sticky=W) #textvariable 为可变标签
liulancaj=Button(root,text='浏览caj',command=liulancajfunc)
liulancaj.grid(row=0,column=1,sticky=E)

pdflb=Label(root,textvariable=pdf).grid(row=1,column=0,sticky=W)
liulanpdf=Button(root,text='浏览pdf',command=liulanpdffunc)
liulanpdf.grid(row=1,column=1,sticky=E)
#转换按钮
zh=Button(root,text='转　换',command=zhuanhuanfunc).grid(row=3,column=0,sticky=E,ipadx=50)
add=Button(root,text='加目录',command=addindex).grid(row=4,column=0,sticky=E,ipadx=50)
root.mainloop()
#a=tkinter.filedialog.askopenfilename()
#print(a)