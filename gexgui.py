from tkinter import *
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc

IMG_H = 1000
def clickButton():
	global canvas
	ticker = e1.get().upper()
	#canvas.create_rectangle(0, 0, 2000, IMG_H, fill='orange')  #should use delete('all')
	#drawTickerOnCanvas( e1.get().upper(), e2.get(), "orange" )
	filename = dc.drawGEXChart(ticker, 40, dte=0)

	image = Image.open("./" + filename)
	tk_image = ImageTk.PhotoImage(image)
	#canvas.create_image(0, 0, image=tk_image)
	canvas.configure(image=tk_image)
	canvas.image = tk_image
	
win = Tk()
win.geometry(str(500) + "x" + str(IMG_H + 45))

Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, "SPY")

e2 = Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '1')

Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')

canvas = Label()
canvas.grid(row=4, column=0, columnspan=40, rowspan=40)

clickButton()
mainloop()
