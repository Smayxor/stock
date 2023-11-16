import datetime
from threading import Timer
import time
import schedule
import tkinter as tk
#from tkinter import Entry, Label, Button, Canvas
import datapuller as dp
import os
import ujson as json #usjon is json written in C

blnRun = True
IMG_H = 500
lastIndex = 0
t = None
previousClose = 0
averageRange = 0
options = dp.getOptionsChain('SPX', 0)
gexList = dp.getGEX(options[1])

def identifyKeyLevels(ticker, strikes):
	global previousClose, averageRange
	price = dp.getQuote(ticker)
	atr = dp.getATR(ticker)
	previousClose = atr[2]
	averageRange = atr[0]
	atrs = atr[1]
	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	strikes = dp.shrinkToCount(strikes, price, 100)
	#maxTotalGEX = max(strikes, key=lambda i: i[1])[1]
	#minTotalGEX = abs(min(strikes, key=lambda i: i[1])[1])
	#maxTotalGEX = max( (maxTotalGEX, minTotalGEX) )
	
	maxTotalOI = max(strikes, key=lambda i: i[2])[2]
	maxCallOI = max(strikes, key=lambda i: i[4])[4]
	maxPutOI = abs(min(strikes, key=lambda i: i[6])[6])
	
	#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk
	keyLevels = []
	oiThreshold = maxTotalOI * 0.6
	callOIThreshold = maxCallOI * 0.25
	putOIThreshold = maxPutOI * 0.25
	totalOIThreshold = callOIThreshold + putOIThreshold
	def addKeyLevel(strike):
		if strike not in keyLevels: keyLevels.append( strike )
	
	for i in range(1, len(strikes) - 1):
		strike = strikes[i]
		if strike[2] > oiThreshold: addKeyLevel( strike[0] )
		#cpRatio = (strike[4] / strike[6])
		#if cpRatio > 0.9 and cpRatio < 0.1 : addKeyLevel( strike[0] )
		if strike[4] > callOIThreshold and strike[6] > putOIThreshold : 
			totalPrev = strikes[i-1][4] + strikes[i-1][6]
			totalMe = strikes[i][4] + strikes[i][6]
			totalNext = strikes[i+1][4] + strikes[i+1][6]
			#if (totalMe > totalPrev * 0.80) and (totalMe > totalNext * 0.80) and (totalMe > totalOIThreshold ):	addKeyLevel( strike[0] )
		
	txtTmp = ''
	for level in keyLevels: txtTmp = txtTmp + "  -  " + str(level)
	print( txtTmp )
identifyKeyLevels('SPX', gexList)

#************ Calced after identifyKeyLevels sets values
previousClose = round(previousClose / dp.SPY2SPXRatio, 2)
averageRange = round(averageRange / dp.SPY2SPXRatio, 2)
highPrice = previousClose + (averageRange * 1.1)
lowPrice = previousClose - (averageRange * 1.1)
priceRange = highPrice - lowPrice
scale = IMG_H / priceRange
#******************************************

def clickButton():
	global canvas, lastIndex
	canvas.delete("all")
	lastIndex = 0

def on_closing():
	global blnRun, timer
	blnRun = False
	timer.cancel()
	win.destroy()

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def timerThread():
	global blnRun
	if not blnRun : return
	drawTickerOnCanvas( e1.get().upper(), e2.get(), "orange" )

def drawTickerOnCanvas( ticker, days, color ):	
	avgs = []
	candles = dp.getCandles('SPY', days, 1)
	#lastClose = 0
	for i in range( len( candles ) ) :
		avgs.append( candles[i]['open'] )
		#avgs.append( candles[i]['close'] )
		#lastClose = candles[i]['close']
	
	try: buyPrice = float(eBuyPrice.get())
	except: buyPrice = 0
	try: sellPrice = float(eSellPrice.get())
	except: sellPrice = 0

	candle = candles[-1]
	lastClose = candle['close']
	lastLow = candle['low']
	lastHigh = candle['high']

	if lastLow <= buyPrice <= lastHigh : print(f'{buyPrice} Within range {lastLow} - {lastHigh}')
	canvas.itemconfig(lastPriceTextObject,text=str(round(lastClose, 2)))
	#print(f'Buy at {buyPrice}, Sell at {sellPrice}' )
	drawAVGs(avgs, 'yellow', lastClose)

def drawAVGs(avgs, color, lastClose):
	global canvas, lastIndex
	#{'open': 450.9499, 'high': 450.9499, 'low': 450.89, 'close': 450.92, 'volume': 2493, 'datetime': 1693612740000}
	lenavgs = len(avgs)
	"""  Find peaks and valleys
	highs = []
	lows = []
	last = avgs[0]
	high = 0
	low = 0
	def checkNextHigh(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] > avgs[index] : return False
		return True
	def checkNextLow(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] < avgs[index] : return False
		return True

	for i in range( 1, lenavgs ) :
		if avgs[i] > avgs[high] and checkNextHigh(i):
			highs.append(i)
			high = i
			low = i
		elif avgs[i] < avgs[low] and checkNextLow(i):
			lows.append(i)
			low = i
			high = i
		else:
			pass
	"""
	def convertY( val ):	return IMG_H - ((val - lowPrice) * scale)
	if lenavgs > 2000 : lenavgs = 2000
	for x in range( 1, lenavgs ):
		if x > lastIndex:
			y1 = convertY(avgs[x-1])
			y2 = convertY(avgs[x])
			canvas.create_line(x-1,y1,x,y2, fill=color, width=1)
			lastIndex = x

	x = lastIndex - 1
	y = convertY(lastClose) - 1
	canvas.coords(lastPriceObject, (x, y, x+2, y+2))
	canvas.coords(lastPriceTextObject, (x + 50, y))
	#print( len( canvas.find("all") ) )

def drawPriceScale():
	canvas.create_line(0, 3, 1850, 3, dash=(1,3), fill="green", width=3)
	canvas.create_line(0, IMG_H / 2, 1850, IMG_H / 2, dash=(1,3), fill="white", width=2)
	canvas.create_line(0, IMG_H, 1850, IMG_H, dash=(1,3), fill="red", width=2)
	canvas.create_text(1850, 10, text=str(highPrice), fill="green")#, font=('Helvetica 15 bold'))
	canvas.create_text(1850, IMG_H / 2 + 10, text=str(previousClose), fill="red")
	canvas.create_text(1850, IMG_H + 10, text=str(lowPrice), fill="red")
	
#50% retracement is to tell you that we are testing whether or not we would even extend. If we retrace more than 50%, then we are unlikely to extend
#(VIX / 16) * ATR * FIB


win = tk.Tk()
win.geometry(str(2000 + 5) + "x" + str(IMG_H + 95 + 50))
win.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = tk.Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, "SPY")

e2 = tk.Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '0')

e3 = tk.Entry(win, width=4)
e3.grid(row=0, column=2, sticky='E')
e3.insert(0, '5')
tk.Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')

tk.Label(win, text="Interval", width=10).grid(row=0, column=3, sticky='W')
tk.Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=4, sticky='E')

canvas = tk.Canvas(win, width=2000, height=IMG_H + 50)
canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
canvas.configure(bg="#000000")
lastPriceObject = canvas.create_oval(0, 0, 2, 2, fill="blue", outline="#DDD", width=2)
lastPriceTextObject = canvas.create_text(0, 0, text=str(0), fill="blue")

tk.Label(win, text="BuyPrice", width=10).grid(row=25, column=0, sticky="W")
eBuyPrice = tk.Entry(win, width=8)
eBuyPrice.grid(row=25, column=0, sticky="E")
tk.Label(win, text="SellPrice", width=10).grid(row=25, column=1, sticky="W")
eSellPrice = tk.Entry(win, width=8)
eSellPrice.grid(row=25, column=1, sticky="E")

checkCall = tk.IntVar()
cbCall = tk.Checkbutton(win, text='Call',variable=checkCall, onvalue=1, offvalue=0)#, command=print_selection)
cbCall.grid(row=25, column=2, sticky="W")
checkCall.set(1)

drawPriceScale()
timer = RepeatTimer(1, timerThread)
timer.setDaemon(True)  #Solves runtime error using tkinter from another thread
timer.start()
#clickButton()
tk.mainloop()

"""
	highPrice = max(avgs)
	lowPrice = min(avgs)
	priceRange = highPrice - lowPrice
	scale = IMG_H / priceRange
	lenavgs = len(avgs)
	
	highs = []
	lows = []
	last = avgs[0]
	high = 0
	low = 0
	def checkNextHigh(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] > avgs[index] : return False
		return True
	def checkNextLow(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] < avgs[index] : return False
		return True

	for i in range( 1, lenavgs ) :
		if avgs[i] > avgs[high] and checkNextHigh(i):
			highs.append(i)
			high = i
			low = i
		elif avgs[i] < avgs[low] and checkNextLow(i):
			lows.append(i)
			low = i
			high = i
		else:
			pass

	def convertY( val ):	return IMG_H - ((val - lowPrice) * scale)
	if lenavgs > 2000 : lenavgs = 2000
	for x in range( 1, lenavgs ):
		y1 = convertY(avgs[x-1])
		y2 = convertY(avgs[x])
		canvas.create_line(x-1,y1,x,y2, fill=color, width=1)
		
		#volY = IMG_H - ((volumes[x] / maxVolume) * 200) + 50
		#canvas.create_line(x-1, volY, x, IMG_H + 50, fill="blue", width=1)
		
#		if x in highs : canvas.create_line(x-5,convertY(avgs[x]),x+5,convertY(avgs[x]), fill="green", width=5)
#		if x in lows : canvas.create_line(x-5,convertY(avgs[x]),x+5,convertY(avgs[x]), fill="red", width=5)
#50% retracement is to tell you that we are testing whether or not we would even extend. If we retrace more than 50%, then we are unlikely to extend
#(VIX / 16) * ATR * FIB

	#for x in range(1, len(highs)):
	#	canvas.create_line(highs[x-1],convertY(avgs[highs[x-1]]),highs[x],convertY(avgs[highs[x]]), fill="green", width=1)
	#for x in range(1, len(lows)):
	#	canvas.create_line(lows[x-1],convertY(avgs[lows[x-1]]),lows[x],convertY(avgs[lows[x]]), fill="red", width=1)
"""