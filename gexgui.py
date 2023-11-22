import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
from threading import Timer
import time

blnRun = True
IMG_H = 1000
spCoords = [(0, 0), (0, 0), (0, 0)]
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

class CanvasItem():
	Strike = 0
	Y = 0
	callCanvas = None
	putCanvas = None
	def __init__(self, strike, y, callCanvas, putCanvas):
		self.callCanvas = callCanvas
		self.putCanvas = putCanvas
		self.Y = y
		self.Strike = strike

def clickButton():
	global canvas, ticker
	ticker = e1.get().upper()
	
	options = dp.getOptionsChain(ticker, 0)
	gexList = dp.getGEX(options[1])

	filename = dc.drawGEXChart(ticker, 30, dte=0, strikes=gexList, expDate=options[0]) #function needs optional parameter to pass gexdata in
	image = Image.open("./" + filename)
	tk_image = ImageTk.PhotoImage(image)
	canvas.configure(image=tk_image)
	canvas.image = tk_image

	initVChart( gexList, ticker )

def timerThread():
#	global ticker
#	ticker = e1.get().upper()
	
	options = dp.getOptionsChain(ticker, 0)
	gexList = dp.getGEX(options[1])
	refreshVCanvas(strikes=gexList)
	refreshPriceChart()

def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, pcPoly
	vcanvas.delete('all')
	#vcanvas.configure(bg='black')
	price = dp.getQuote(ticker)
	vPrice = price
	strikes = dp.shrinkToCount(strikes, price, 30)
	y = 680
	for strike in strikes:
		vcanvas.create_text( 200, y, fill='white', text=str(round((strike[0]), 2)) )
		canvasCall = vcanvas.create_rectangle(100, y-10, 150, y + 10, fill='green')
		canvasPut = vcanvas.create_rectangle(250, y-10, 300, y + 10, fill='red')
		vcStrikes.append( CanvasItem(strike[dp.GEX_STRIKE], y, canvasCall, canvasPut) )
		y -= 20
	refreshVCanvas(strikes = strikes)

	global previousClose, averageRange, highPrice, lowPrice, priceRange, scale, lastPriceIndex
	price = dp.getQuote(ticker)
	atr = dp.getATR(ticker)
	previousClose = atr[2]
	averageRange = atr[0]
	atrs = atr[1]

	previousClose = round(previousClose, 2)
	averageRange = round(averageRange, 2)
	highPrice = previousClose + (averageRange * 1.1)
	lowPrice = previousClose - (averageRange * 1.1)
	priceRange = highPrice - lowPrice
	scale = 300 / priceRange

	print( ticker, price, scale, lowPrice, highPrice, averageRange, previousClose )

	scanvas.delete('all')
	pcPoly = scanvas.create_polygon(fill="blue", *spCoords)
	lastPriceIndex = 0
	refreshPriceChart()

def convertY( val ):	return 300 - ((val - lowPrice) * scale)

def refreshPriceChart():
	global scanvas, lastPriceIndex
	
	avgs = []
	candles = dp.getCandles(ticker, 0, 1)
	for i in range( len( candles ) ) :
		avgs.append( candles[i]['open'] )

	candle = candles[-1]
	lastClose = candle['close']
	lastLow = candle['low']
	lastHigh = candle['high']

	#scanvas.itemconfig(lastPriceTextObject,text=str(round(lastClose, 2)))
	lenavgs = len(avgs)

	if lenavgs > 2000 : lenavgs = 2000
	for x in range( 1, lenavgs ):
		if x > lastPriceIndex:
			y1 = convertY(avgs[x-1])
			y2 = convertY(avgs[x])
			#print(f'Drawing at {x} x {y2}')
			scanvas.create_line(x-1,y1,x,y2, fill='blue', width=1)
			lastPriceIndex = x

	x = lastPriceIndex - 1
	y = convertY(lastClose) - 1
	#scanvas.coords(lastPriceObject, (x, y, x+2, y+2))
	#scanvas.coords(lastPriceTextObject, (x + 50, y))

def refreshVCanvas(strikes = None):
	calcVals = []
	for strike in strikes:
		callSize = abs(strike[dp.GEX_CALL_OI] - strike[dp.GEX_CALL_VOLUME])
		putSize = abs(strike[dp.GEX_PUT_OI] - strike[dp.GEX_PUT_VOLUME])
		calcVals.append( (strike[dp.GEX_STRIKE], callSize, putSize) )
		
	maxCallOI = max(calcVals, key=lambda i: i[1])[1]
	maxPutOI = abs( min(calcVals, key=lambda i: i[2])[2] )
	maxCallPutOI = max( (maxCallOI, maxPutOI) )
	maxSize = 50
	for vcItem in vcStrikes:
		strike = next(x for x in calcVals if x[0] == vcItem.Strike)
		#vcanvas.itemconfig( vcItem.callCanvas, fill='white')
		callSize = (strike[1] / maxCallPutOI) * maxSize
		putSize = (strike[2] / maxCallPutOI) * maxSize
		vcanvas.coords(vcItem.callCanvas, 170-callSize, vcItem.Y - 10, 170, vcItem.Y + 10)
		vcanvas.coords(vcItem.putCanvas, 230, vcItem.Y - 10, 230 + putSize, vcItem.Y + 10)
		
def on_closing():
	global blnRun, timer
	blnRun = False
	timer.cancel()
	win.destroy()

class RepeatTimer(Timer):
	def run(self):
		self.interval = 2
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)
	
win = tk.Tk()
win.geometry(str(1000) + "x" + str(IMG_H + 45))
win.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = tk.Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, ticker)

e2 = tk.Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '1')

tk.Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
tk.Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')

canvas = tk.Label()
canvas.grid(row=1, column=0)#, columnspan=20, rowspan=20)

vcanvas = tk.Canvas()
vcanvas.grid(row=1, column=1, columnspan=2)#, rowspan=20)
vcanvas.configure(width=500, height=700, bg='black')

scanvas = tk.Canvas()
scanvas.grid(row=2, column=0, columnspan=4)#, rowspan=40)
scanvas.configure(width=1000, height=300, bg='black')

clickButton()
timer = RepeatTimer(1, timerThread)
timer.setDaemon(True)  #Solves runtime error using tkinter from another thread
timer.start()

tk.mainloop()
