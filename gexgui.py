import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
from threading import Timer
import time

blnRun = True
IMG_H = 1000
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
SCANVAS_HEIGHT = 300

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

blnReset = True
def clickButton():
	global blnReset
	blnReset = True

def triggerReset():
	global canvas, ticker, blnReset
	blnReset = False
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
	if blnReset: triggerReset()
	options = dp.getOptionsChain(ticker, 0)
	gexList = dp.getGEX(options[1])
	refreshVCanvas(strikes=gexList)
	try:	refreshPriceChart()
	except: pass

def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, vcStrikes
	vcanvas.delete('all')
	del vcStrikes
	vcStrikes = []
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
	scale = SCANVAS_HEIGHT / priceRange

	scanvas.delete('all')
	#pcPoly = scanvas.create_polygon(fill="yellow", *spCoords, width=3)
	lastPriceIndex = 0
	refreshPriceChart()#	try:
#	except: pass
	
def convertY( val ):	return SCANVAS_HEIGHT - ((val - lowPrice) * scale)

lastPriceRect, lastPriceLine = None, None
def refreshPriceChart():
	global scanvas, lastPriceIndex, lastPriceRect, lastPriceLine
	#lowestValue = 9999
	if ticker == 'SPX':
		candles = dp.getRecentCandles('SPY', 1)
		for x in candles:
			x['open'] *= dp.SPY2SPXRatio
			x['high'] *= dp.SPY2SPXRatio
			x['low'] *= dp.SPY2SPXRatio
			x['close'] *=  dp.SPY2SPXRatio
			#lowestValue = min([lowestValue, x['open'], x['high'], x['low'], x['close']])
	else:
		candles = dp.getRecentCandles(ticker, 1)
	#print( lowestValue )
	#print(f'{len(candles)} Candles Found')
	def getCandleCoords(candle):
		o = convertY(candle['open'])
		c = convertY(candle['close'])
		h = convertY(candle['high'])
		l = convertY(candle['low'])
		colr = 'green' if o >= c  else 'red'
		if o > c :
			tmp = c
			c = o
			o = tmp
		o -= 1
		c += 1
		return (o, c, h, l, colr)
	i = 0
	for candle in candles:
		if i > lastPriceIndex:
			x = i * 5
			coords = getCandleCoords(candle)
			#print(f'Drawing Candle {coords}')
			lastPriceRect = scanvas.create_rectangle([x,coords[0], x+5, coords[1]], fill=coords[4])
			lastPriceLine = scanvas.create_line([x+3,coords[2]-1, x+3, coords[3]+1], fill=coords[4])
			lastPriceIndex = i
		i += 1

	candle = candles[-1]
	x = (i-1) * 5
	coords = getCandleCoords(candle)
	scanvas.coords(lastPriceRect, (x,coords[0], x+5, coords[1]))
	scanvas.coords(lastPriceLine, (x+3,coords[2]-1, x+3, coords[3]+1))


	win.title( candle['close'] )
	#print(f'{len(scanvas.find("all"))} items on canvas')
	#x = lastPriceIndex - 1
	#y = convertY(lastClose) - 1
	#scanvas.coords(lastPriceObject, (x, y, x+2, y+2))
	#scanvas.coords(lastPriceTextObject, (x + 50, y))

def refreshVCanvas(strikes = None):
	calcVals = []
	for strike in strikes:
		callSize = abs(strike[dp.GEX_CALL_OI] - strike[dp.GEX_CALL_VOLUME])# * (strike[dp.GEX_CALL_BID_SIZE] / strike[dp.GEX_CALL_ASK_SIZE])
		putSize = abs(strike[dp.GEX_PUT_OI] - strike[dp.GEX_PUT_VOLUME])# * (strike[dp.GEX_PUT_BID_SIZE] / strike[dp.GEX_PUT_ASK_SIZE])
		calcVals.append( (strike[dp.GEX_STRIKE], callSize, putSize) )
		
	maxCallOI = max(calcVals, key=lambda i: i[1])[1]
	maxPutOI = abs( min(calcVals, key=lambda i: i[2])[2] )
	maxCallPutOI = max( (maxCallOI, maxPutOI) )
	maxSize = 50
	#print(calcVals)
	for vcItem in vcStrikes:
		#print( vcItem.Strike )
		strike = next(x for x in calcVals if x[0] == vcItem.Strike)
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
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		
	def run(self):#, daemon=True):
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
scanvas.configure(width=1000, height=SCANVAS_HEIGHT, bg='black')

timer = RepeatTimer(1, timerThread, daemon=True)
timer.start()

tk.mainloop()
