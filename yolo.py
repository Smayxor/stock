import datetime
from threading import Timer
import time
import schedule
import tkinter as tk
import datapuller as dp
import os
import ujson as json #usjon is json written in C

blnRun = True
IMG_H = 500
lastIndex = 0
previousClose = 0
averageRange = 0
options = dp.getOptionsChain('SPX', 0)
gexList = dp.getGEX(options[1])

balance = dp.getAccountBalance()['cash']
print(f'Account Balance {balance}')
print(f'Open positions {dp.getPositions()}')
print(f'Open orders {dp.getOrders()}')

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
		if strike[dp.GEX_TOTAL_OI] > oiThreshold: addKeyLevel( strike[dp.GEX_STRIKE] )
		#cpRatio = (strike[4] / strike[6])
		#if cpRatio > 0.9 and cpRatio < 0.1 : addKeyLevel( strike[0] )
		if strike[dp.GEX_CALL_OI] > callOIThreshold and strike[dp.GEX_PUT_OI] > putOIThreshold : 
			totalPrev = strikes[i-1][dp.GEX_CALL_OI] + strikes[i-1][dp.GEX_PUT_OI]
			totalMe = strikes[i][dp.GEX_CALL_OI] + strikes[i][dp.GEX_PUT_OI]
			totalNext = strikes[i+1][dp.GEX_CALL_OI] + strikes[i+1][dp.GEX_PUT_OI]
			if (totalMe > totalPrev * 0.80) and (totalMe > totalNext * 0.80) and (totalMe > totalOIThreshold ):	addKeyLevel( strike[0] )

	for x in range(len(keyLevels)):
		keyLevels[x] = round(keyLevels[x] / dp.SPY2SPXRatio, 2)
	
	return keyLevels
keyLevels = identifyKeyLevels('SPX', gexList)

#************ Calced after identifyKeyLevels sets values
previousClose = round(previousClose / dp.SPY2SPXRatio, 2)
averageRange = round(averageRange / dp.SPY2SPXRatio, 2)
highPrice = previousClose + (averageRange * 1.5)
lowPrice = previousClose - (averageRange * 1.5)
keyLevels.append(previousClose + averageRange)
keyLevels.append(previousClose)
keyLevels.append(previousClose - averageRange)
priceRange = highPrice - lowPrice
scale = IMG_H / priceRange
print(f'PC {previousClose} - ATR {averageRange} - Low {lowPrice} - High {highPrice}')
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
#		self.interval = 2
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

def convertY( val ):	return IMG_H - ((val - lowPrice) * scale)

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

	for key in keyLevels:
		y = convertY(key)
		#print( f'{key} drawn at {y}')
		canvas.create_line(0, y, 750, y, dash=(1,3), fill="white", width=1)
		canvas.create_text(780, y, text=str(key), fill="white" )
		print( key, y )
"""
	canvas.create_line(0, 3, 750, 3, dash=(1,3), fill="green", width=3)
	canvas.create_line(0, IMG_H / 2, 750, IMG_H / 2, dash=(1,3), fill="white", width=2)
	canvas.create_line(0, IMG_H, 750, IMG_H, dash=(1,3), fill="red", width=2)
	canvas.create_text(750, 10, text=str(highPrice), fill="green")#, font=('Helvetica 15 bold'))
	canvas.create_text(750, IMG_H / 2 + 10, text=str(previousClose), fill="red")
	canvas.create_text(750, IMG_H + 10, text=str(lowPrice), fill="red")
"""

#50% retracement is to tell you that we are testing whether or not we would even extend. If we retrace more than 50%, then we are unlikely to extend
#(VIX / 16) * ATR * FIB

win = tk.Tk()
win.geometry(str(880 + 5) + "x" + str(IMG_H + 95 + 50))
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
tk.Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=4, sticky='W')

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
tk.mainloop()

#50% retracement is to tell you that we are testing whether or not we would even extend. If we retrace more than 50%, then we are unlikely to extend
#(VIX / 16) * ATR * FIB
