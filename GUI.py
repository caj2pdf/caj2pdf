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
	origincaj=tkinter.filedialog.askopenfilename(filetypes=[('CAJ','caj'),('所有文件','**')],initialdir='D:\Dropbox\Github\caj2pdf')
	#print(origincaj[0:-3]+'pdf')
	caj.set(os.path.basename(origincaj)) #显示caj文件名
def liulanpdffunc():
	#print('2')
	global originpdf
	originpdf=tkinter.filedialog.askopenfilename(filetypes=[('PDF','pdf'),('所有文件','**')],initialdir=pdfpath.get())
	pdf.set(os.path.basename(originpdf)) #显示pdf文件名
def zhuanhuanfunc():
	global originpdf
	global origincaj
	try:
		cajzh = CAJParser(origincaj)
		print('now conert start')
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
		tmp=os.path.dirname(originpdf)+'/'+'tmp.pdf'
		print(tmp)
		add_outlines(toc, originpdf, tmp)
		#pdfname=os.path.basename(originpdf)#获取待加目录pdf的文件名
		#base=os.path.dirname(originpdf)#获取待加目录pdf的路径
		os.replace(tmp,originpdf)
		#print('replace')  #调试用的
		messagebox.showinfo('提示','完成')
	except:
		messagebox.showinfo('错误','请检查是否选中caj或pdf')

'''def center_window(w, h):
    #窗口居中
    # get screen width and height  
    ws = root.winfo_screenwidth()  
    hs = root.winfo_screenheight()  
    # calculate position x, y  
    x = (ws/2) - (w/2)     
    y = (hs/2) - (h/2)  
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))'''

root=Tk()
#root.maxsize(200,150)
#设置可变的标签内容
#center_window(200,150)#x*y

caj=StringVar()
caj.set('caj')
pdf=StringVar()
#pdf.set('pdf')
#生成浏览标签及按钮
cajlb=Label(root,textvariable=caj)
cajlb.grid(row=0,column=0,sticky=W) #textvariable 为可变标签
liulancaj=Button(root,text='浏览caj',command=liulancajfunc)
liulancaj.grid(row=0,column=1,sticky=E)

#pdflb=Label(root,textvariable=pdf).grid(row=1,column=0,sticky=W)
#路径
pdfpath=Entry(root,textvariable=pdf)
pdfpath.grid(row=1,column=0,sticky=W+E)

liulanpdf=Button(root,text='浏览pdf',command=liulanpdffunc)
liulanpdf.grid(row=1,column=1,rowspan=2,sticky=E)


#转换按钮
zh=Button(root,text='转　换',command=zhuanhuanfunc)
zh.grid(row=4,column=0,sticky=W+E,ipadx=50)
add=Button(root,text='加目录',command=addindex)
add.grid(row=5,column=0,sticky=W+E,ipadx=50)
root.mainloop()
#a=tkinter.filedialog.askopenfilename()
#print(a)