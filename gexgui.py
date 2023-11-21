import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc

IMG_H = 1000
def clickButton():
	global canvas
	ticker = e1.get().upper()
	#canvas.create_rectangle(0, 0, 2000, IMG_H, fill='orange')  #should use delete('all')
	#drawTickerOnCanvas( e1.get().upper(), e2.get(), "orange" )
	filename = dc.drawGEXChart(ticker, 30, dte=0)

	image = Image.open("./" + filename)
	tk_image = ImageTk.PhotoImage(image)
	#canvas.create_image(0, 0, image=tk_image)
	canvas.configure(image=tk_image)
	canvas.image = tk_image
	
win = tk.Tk()
win.geometry(str(1000) + "x" + str(IMG_H + 45))

tk.Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = tk.Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, "SPX")

e2 = tk.Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '1')

tk.Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
tk.Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')

canvas = tk.Label()
canvas.grid(row=1, column=0)#, columnspan=20, rowspan=20)

vcanvas = tk.Canvas()
vcanvas.grid(row=1, column=1, columnspan=2)#, rowspan=20)
vcanvas.configure(width=500, height=750)
vcanvas.create_rectangle(0, 0, 2000, IMG_H, fill='blue')

scanvas = tk.Canvas()
scanvas.grid(row=2, column=0, columnspan=4)#, rowspan=40)
scanvas.configure(width=1000, height=250)
scanvas.create_rectangle(0, 0, 2000, IMG_H, fill='yellow')

clickButton()
tk.mainloop()
