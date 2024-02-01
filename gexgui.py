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
	global canvas, ticker, blnReset
	blnReset = False
	ticker = e1.get().upper()
	
	try:
		gexData = dp.pullLogFile(fileToday)
		gexList = list(gexData.values())[-1]
		#print(1)
		filename = dc.drawGEXChart("SPX", 30, dte=0, strikes=gexList, expDate=0, targets=True) #function needs optional parameter to pass gexdata in
		#print(2)
		image = Image.open("./" + filename)
		tk_image = ImageTk.PhotoImage(image)
		canvas.configure(image=tk_image)
		canvas.image = tk_image
		#print(3)
		initVChart( gexList, "SPX" )
		#print(4)
		filename = dc.drawPriceChart("SPX", fileToday, gexData, [e3.get(), e4.get()])
		if 'error' in filename: return
		image = Image.open("./" + filename)
		tk_image = ImageTk.PhotoImage(image)
		strikecanvas.configure(image=tk_image)
		strikecanvas.image = tk_image
	except Exception as error:
		print("An exception occurred:", error)

def timerThread():
	if blnReset: triggerReset()
	dte = e2.get()
	if not dte.isnumeric(): dte = 0
	try:
		#options = dp.getOptionsChain(ticker, int(dte))
		#gexList = dp.getGEX(options[1])
		gexData = dp.pullLogFile(fileToday)
		gexList = list(gexData.values())[-1]
		#print('Timer Thread 1')
		refreshVCanvas(strikes=gexList)
		#print('Timer Thread 2')

		price = dp.getPrice( "SPX", gexList, 0 )
		win.title( f'Price ${price}')

		filename = dc.drawPriceChart("SPX", fileToday, gexData, [e3.get(), e4.get()])
		if 'error' in filename: return
		image = Image.open("./" + filename)
		tk_image = ImageTk.PhotoImage(image)
		strikecanvas.configure(image=tk_image)
		strikecanvas.image = tk_image
	except:
		print( 'Error ', dte )
		
		
def on_strike_click(event):
	global vcStrikes
	if event.y < 73: 
		e3Text.set('all')
		return
	index = (685 - event.y) // 20
	endText = 'c' if event.x < 67 else 'p'
	text = str(vcStrikes[index].Strike).split('.')[0] + endText
	if endText == 'c' : e3Text.set(text)
	else: e4Text.set(text)

def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, vcStrikes
	vcanvas.delete('all')
	del vcStrikes
	vcStrikes = []
	firstStrike = strikes[0]
	#print('init start')
	price = dp.getPrice("SPX", strikes) #firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)  #dp.getQuote(ticker)
	vPrice = price
	#print('init 1')
	strikes = dp.shrinkToCount(strikes, price, 30)
	#print('init 2')
	y = 680
	for strike in strikes:
		txt = str(round((strike[0]), 2))
		canvasStrikeText = vcanvas.create_text( 70, y, fill='white', text=txt, tag=txt )
		vcanvas.tag_bind(txt, '<Button-1>', on_strike_click)
		canvasCall = vcanvas.create_rectangle(0, y-10, 50, y + 10, fill='green')
		canvasCallVol = vcanvas.create_rectangle(0, y-10, 100, y, fill='blue')

		canvasPut = vcanvas.create_rectangle(90, y-10, 150, y + 10, fill='red')
		canvasPutVol = vcanvas.create_rectangle(90, y-10, 150, y, fill='yellow')
		
		canvasCallPrice = vcanvas.create_text(3, y, fill='red', anchor="w", text=str(round((strike[dp.GEX_CALL_BID]), 2)))
		canvasPutPrice = vcanvas.create_text(130, y, fill='green', anchor="w", text=str(round((strike[dp.GEX_PUT_BID]), 2)))
		
		vcStrikes.append( CanvasItem(strike[dp.GEX_STRIKE], y, canvasCall, canvasPut, canvasCallVol, canvasPutVol, canvasCallPrice, canvasPutPrice, canvasStrikeText) )
		y -= 20
		
	allTarget = vcanvas.create_text( 70, y, fill='white', text='Show-All', tag='Show-All' )
	vcanvas.tag_bind('Show-All', '<Button-1>', on_strike_click)
	#print('init 3')
	refreshVCanvas(strikes = strikes)
	#print('init done')
	
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
vcanvas.place(x=500, y=40)
vcanvas.configure(width=150, height=700, bg='black')

strikecanvas = tk.Label()
strikecanvas.place(x=652, y=40)

timer = dp.RepeatTimer(20, timerThread, daemon=True)
timer.start()
timerThread()

tk.mainloop()
