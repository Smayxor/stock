import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
from threading import Timer
import time
import math

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

	options = dp.getOptionsChain(ticker, 1)
	gexList = dp.getGEX(options[1])

	initVChart( gexList, ticker )
	loadStrikeChart()
	
def loadStrikeChart():
	try:
		fileList = [x for x in dp.pullLogFileList() if ((ticker=='SPX') ^ ('SPY' in x))]
		file = fileList[-1]
		gexData = dp.pullLogFile(file)
		filename = dc.drawPriceChart(ticker, file, gexData, [e3.get()])
		if 'error' in filename: return
		image = Image.open("./" + filename)
		tk_image = ImageTk.PhotoImage(image)
		strikecanvas.configure(image=tk_image)
		strikecanvas.image = tk_image
	except:
		pass

def timerThread():
	if blnReset: triggerReset()
	dte = e2.get()
	if not dte.isnumeric(): dte = 0
	try:
		options = dp.getOptionsChain(ticker, int(dte))
		gexList = dp.getGEX(options[1])
		refreshVCanvas(strikes=gexList)
		loadStrikeChart()	

		price = dp.getPrice( ticker, gexList, options[0] )
		win.title( f'Price ${price}')
	except:
		print( 'Error ', dte )
		
def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, vcStrikes
	vcanvas.delete('all')
	del vcStrikes
	vcStrikes = []
	firstStrike = strikes[0]
	price = firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)  #dp.getQuote(ticker)
	vPrice = price
	strikes = dp.shrinkToCount(strikes, price, 30)
	y = 680
	for strike in strikes:
		canvasStrikeText = vcanvas.create_text( 70, y, fill='white', text=str(round((strike[0]), 2)) )
		canvasCall = vcanvas.create_rectangle(0, y-10, 50, y + 10, fill='green')
		canvasCallVol = vcanvas.create_rectangle(0, y-10, 100, y, fill='blue')

		canvasPut = vcanvas.create_rectangle(90, y-10, 150, y + 10, fill='red')
		canvasPutVol = vcanvas.create_rectangle(90, y-10, 150, y, fill='yellow')
		
		canvasCallPrice = vcanvas.create_text(3, y, fill='red', anchor="w", text=str(round((strike[dp.GEX_CALL_BID]), 2)))
		canvasPutPrice = vcanvas.create_text(130, y, fill='green', anchor="w", text=str(round((strike[dp.GEX_PUT_BID]), 2)))
		
		vcStrikes.append( CanvasItem(strike[dp.GEX_STRIKE], y, canvasCall, canvasPut, canvasCallVol, canvasPutVol, canvasCallPrice, canvasPutPrice, canvasStrikeText) )
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
		candles = dp.getRecentCandles('SPX', 1)
#		for x in candles:
#			x['open'] *= dp.SPY2SPXRatio
#			x['high'] *= dp.SPY2SPXRatio
#			x['low'] *= dp.SPY2SPXRatio
#			x['close'] *=  dp.SPY2SPXRatio
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

class RepeatTimer(Timer):
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		
	def run(self):#, daemon=True):
		self.interval = 2
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)
	
win = tk.Tk()
win.geometry(str(1100) + "x" + str(IMG_H + 45))
win.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(win, text="               Ticker", width=10).grid(row=0, column=0, sticky='W')
e1 = tk.Entry(win, width=6)
e1.grid(row=0, column=0, sticky='W')
e1.insert(0, ticker)

tk.Label(win, text="                 Days", width=10).grid(row=0, column=0)#, sticky='E')
e2 = tk.Entry(win, width=4)
e2.grid(row=0, column=0)#, sticky='E')
e2.insert(0, '0')

e3 = tk.Entry(win, width=8)
e3.grid(row=0, column=0, sticky='E')
e3.insert(0, '4900c')

tk.Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')

canvas = tk.Label()
canvas.grid(row=1, column=0)#, columnspan=20, rowspan=20)

vcanvas = tk.Canvas()
vcanvas.grid(row=1, column=1, columnspan=1)#, rowspan=20)
vcanvas.configure(width=150, height=700, bg='black')

strikecanvas = tk.Label()
strikecanvas.grid(row=1, column=2, columnspan=1)

scanvas = tk.Canvas()
scanvas.grid(row=2, column=0, columnspan=4)#, rowspan=40)
scanvas.configure(width=1000, height=SCANVAS_HEIGHT, bg='black')

timer = RepeatTimer(1, timerThread, daemon=True)
timer.start()

tk.mainloop()
