import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
from threading import Timer
import time
import math

blnRun = True
IMG_H = 700
vPrice = 0
vcStrikes = []
lastPriceIndex = 0
previousClose = 0
averageRange = 0
highPrice = 0
lowPrice = 0
priceRange = 0
scale = 0
ticker = 'SPX'
blnReset = True
fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
fileToday = fileList[-1]
pcData = []

pcFloatingX = 0
pcFloatingY = 0
pcFloatingText = None
pcFloatingDot = None
strikeCanvasImage, pc_tk_image, pc_image = None, None, None

class CanvasItem():
	Strike = 0
	Y = 0
	callCanvas = None
	putCanvas = None
	callVolCanvas = None
	putVolCanvas = None
	callPriceText = None
	putPriceText =  None
	strikeText = None
	def __init__(self, strike, y, callCanvas, putCanvas, callVolCanvas, putVolCanvas, callPriceText, putPriceText, strikeText):
		self.callCanvas = callCanvas
		self.putCanvas = putCanvas
		self.callVolCanvas = callVolCanvas
		self.putVolCanvas = putVolCanvas
		self.callPriceText = callPriceText
		self.putPriceText = putPriceText
		self.Y = y
		self.Strike = strike
		self.strikeText = strikeText

def clickButton():
	global blnReset
	blnReset = True

def triggerReset():
	global canvas, ticker, blnReset, strikeCanvasImage, pc_tk_image, pc_image
	global pcData, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingDot
	blnReset = False
	ticker = e1.get().upper()
	
	try:
		gexData = dp.pullLogFile(fileToday)
		gexList = list(gexData.values())[-1]
		
		filename = dc.drawGEXChart("SPX", 30, dte=0, strikes=gexList, expDate=0, targets=True) #function needs optional parameter to pass gexdata in
		image = Image.open("./" + filename)
		resize_image = image.resize((400,605))
		tk_image = ImageTk.PhotoImage(resize_image)
		canvas.configure(image=tk_image)
		canvas.image = tk_image
		
		initVChart( gexList, "SPX" )
	
		tmp = dc.drawPriceChart("SPX", fileToday, gexData, [e3.get(), e4.get()], includePrices = True)
		pcData = tmp[1]
		filename = tmp[0]
		if 'error' in filename: return
		pc_image = Image.open("./" + filename)
		pc_tk_image = ImageTk.PhotoImage(pc_image)
		strikecanvas.delete(strikeCanvasImage)
		strikeCanvasImage = strikecanvas.create_image(1600,800,image=pc_tk_image, anchor=tk.NW)
		#strikecanvas.configure(width= 2600, height= 2800)
		#strikecanvas.configure(image=pc_tk_image)
		#strikecanvas.image = pc_tk_image
		#pcFloatingText = strikecanvas.create_text( 1400, 0, fill='yellow', text=e3.get(), tag='float' )
		#pcFloatingDot = strikecanvas.create_oval(1400, 0, 1405, 5, width = 3)
		#setPCFloat(-1,-1)
	except Exception as error:
		print("An exception occurred:", error)

def timerThread():
	global pcData, pcFloatingX, pcFloatingY, pcFloatingText, strikeCanvasImage, pc_tk_image, pc_image
	if blnReset: triggerReset()
	dte = e2.get()
	if not dte.isnumeric(): dte = 0
	try:
		gexData = dp.pullLogFile(fileToday)
		gexList = list(gexData.values())[-1]
		refreshVCanvas(strikes=gexList)

		price = dp.getPrice( "SPX", gexList, 0 )
		win.title( f'Price ${price}')

		tmp = dc.drawPriceChart("SPX", fileToday, gexData, [e3.get(), e4.get()], includePrices = True)
		pcData = tmp[1]
		filename = tmp[0]
		if 'error' in filename: return
		pc_image = Image.open("./" + filename)
		pc_tk_image = ImageTk.PhotoImage(pc_image)
		strikecanvas.delete(strikeCanvasImage)
		strikeCanvasImage = strikecanvas.create_image(0,0,image=pc_tk_image, anchor=tk.NW)
		#strikecanvas.configure(image=pc_tk_image)
		#strikecanvas.image = pc_tk_image
	except Exception as error:
		print( 'Error ', error )
	
def setPCFloat(x, y):
	global pcData, pcFloatingX, pcFloatingY, pcFloatingText
	return
	if pcFloatingText == None : return
	if x == -1:
		firstPCData = pcData[0]
		x = len(firstPCData)

def on_strike_click(event):
	global vcStrikes
	if event.y < 73: 
		e3Text.set('all')
	else :
		index = (685 - event.y) // 20
		endText = 'c' if event.x < 67 else 'p'
		text = str(vcStrikes[index].Strike).split('.')[0] + endText
		if endText == 'c' : e3Text.set(text)
		else: e4Text.set(text)
	timerThread()

def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, vcStrikes
	vcanvas.delete('all')
	del vcStrikes
	vcStrikes = []
	firstStrike = strikes[0]
	price = dp.getPrice("SPX", strikes) 
	vPrice = price
	strikes = dp.shrinkToCount(strikes, price, 30)
	y = 680
	for strike in strikes:
		txt = str(round((strike[0]), 2))
		canvasStrikeText = vcanvas.create_text( 70, y, fill='white', text=txt, tag='widget' )
		#vcanvas.tag_bind('widget', '<Button-1>', on_strike_click)
		canvasCall = vcanvas.create_rectangle(0, y-10, 50, y + 10, fill='green', tag='widget')
		canvasCallVol = vcanvas.create_rectangle(0, y-10, 100, y, fill='blue', tag='widget')

		canvasPut = vcanvas.create_rectangle(90, y-10, 150, y + 10, fill='red', tag='widget')
		canvasPutVol = vcanvas.create_rectangle(90, y-10, 150, y, fill='yellow', tag='widget')
		
		canvasCallPrice = vcanvas.create_text(3, y, fill='red', anchor="w", text=str(round((strike[dp.GEX_CALL_BID]), 2)), tag='widget')
		canvasPutPrice = vcanvas.create_text(130, y, fill='green', anchor="w", text=str(round((strike[dp.GEX_PUT_BID]), 2)), tag='widget')
		
		vcStrikes.append( CanvasItem(strike[dp.GEX_STRIKE], y, canvasCall, canvasPut, canvasCallVol, canvasPutVol, canvasCallPrice, canvasPutPrice, canvasStrikeText) )
		y -= 20
		
	allTarget = vcanvas.create_text( 70, y, fill='white', text='Show-All', tag='widget' )
	vcanvas.tag_bind('widget', '<Button-1>', on_strike_click)
	refreshVCanvas(strikes = strikes)
	
def convertY( val ):	return SCANVAS_HEIGHT - ((val - lowPrice) * scale)

	
def refreshVCanvas(strikes = None):  #VCanvas is  GEX Volume chart on right side
	calcVals = []
	for strike in strikes:
		coi = strike[dp.GEX_CALL_OI]
		poi = strike[dp.GEX_PUT_OI]
		cv = strike[dp.GEX_CALL_VOLUME]
		pv = strike[dp.GEX_PUT_VOLUME]
		cb = strike[dp.GEX_CALL_BID]
		pb = strike[dp.GEX_PUT_BID]
		calcVals.append( (strike[dp.GEX_STRIKE], coi, poi, cv, pv, cb, pb) )
		
	maxCallOI = max(calcVals, key=lambda i: i[1])[1]
	maxPutOI = abs( min(calcVals, key=lambda i: i[2])[2] )
	maxCallPutOI = max( (maxCallOI, maxPutOI) )
	
	maxCallVolume = max(calcVals, key=lambda i: i[3])[3]
	maxPutVolume = abs( min(calcVals, key=lambda i: i[4])[4] )
	maxCallPutVolume = max( (maxCallVolume, maxPutVolume) )
	
	maxCallPutOI = max( [maxCallPutOI, maxCallPutVolume] )
	
	maxSize = 50
	#print(calcVals)
	for vcItem in vcStrikes:
		#print( vcItem.Strike )
		strike = next(x for x in calcVals if x[0] == vcItem.Strike)
		
		callSize = (strike[1] / maxCallPutOI) * maxSize
		putSize = (strike[2] / maxCallPutOI) * maxSize
		vcanvas.coords(vcItem.callCanvas, 50-callSize, vcItem.Y - 10, 50, vcItem.Y + 10)
		vcanvas.coords(vcItem.putCanvas, 90, vcItem.Y - 10, 90 + putSize, vcItem.Y + 10)
		
		callSize = (strike[3] / maxCallPutOI) * maxSize
		putSize = (strike[4] / maxCallPutOI) * maxSize
		vcanvas.coords(vcItem.callVolCanvas, 50-callSize, vcItem.Y - 10, 50, vcItem.Y)
		vcanvas.coords(vcItem.putVolCanvas, 90, vcItem.Y - 10, 90 + putSize, vcItem.Y)
		
		vcanvas.itemconfig(vcItem.callPriceText, text=str(round((strike[5]), 2)))
		vcanvas.itemconfig(vcItem.putPriceText, text=str(round((strike[6]), 2)))

		vcanvas.itemconfig(vcItem.strikeText, text=str(round((strike[0]), 2)))

def on_closing():
	global blnRun, timer
	blnRun = False
	timer.cancel()
	win.destroy()

win = tk.Tk()
win.geometry(str(2200) + "x" + str(IMG_H + 45))
win.protocol("WM_DELETE_WINDOW", on_closing)

e1 = tk.Entry(win, width=6)
e1.insert(0, ticker)
e1.place(x=2, y=0)

lblTicker = tk.Label(win, text="Ticker", width=10)
lblTicker.place(x=30, y=0)

lblDays = tk.Label(win, text="Days", width=10)
lblDays.place(x=130, y=0)

e2 = tk.Entry(win, width=4)
e2.place(x=100, y=0)
e2.insert(0, '0')

e3Text = tk.StringVar() 
e3Text.set("all") 
e3 = tk.Entry(win, width=8, textvariable=e3Text)
e3.place(x=500, y=0)

e4Text = tk.StringVar() 
e4Text.set("4850p")
e4 = tk.Entry(win, width=8, textvariable=e4Text)
e4.place(x=555, y=0)

btnFetch = tk.Button(win, text="Fetch", command=clickButton, width=5)
btnFetch.place(x=652, y=0)

canvas = tk.Label()
canvas.place(x=0, y=40)

vcanvas = tk.Canvas()
vcanvas.place(x=400, y=40)
vcanvas.configure(width=150, height=700, bg='black')

strikecanvas = tk.Canvas(win,width= 1500, height=550, bg='black')
strikecanvas.place(x=552, y=40)
#strikecanvas.configure(width= 2600, height= 2800)

timer = dp.RepeatTimer(20, timerThread, daemon=True)
timer.start()
timerThread()

tk.mainloop()
