import datetime
import threading
import time
import schedule
from tkinter import *
import datapuller as dp
import os
import ujson as json #usjon is json written in C

blnRun = True
IMG_H = 500

def timerThread():
	pass


"""options = dp.getOptionsChain('SPX', 0)
gexList = dp.getGEX(options[1])

def identifyKeyLevels(ticker, strikes):
	price = dp.getQuote(ticker)
	atr = dp.getATR(ticker)
	atrs = atr[1]
	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	strikes = dp.shrinkToCount(strikes, price, 100)
	print( atr )
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
"""
def clickButton():
	global canvas
	#canvas.create_rectangle(0, 0, 2000, IMG_H + 50, fill='black')
	canvas.delete("all")
	drawTickerOnCanvas( e1.get().upper(), e2.get(), "orange" )

def prepData( strikePrice, call ):
	#candles = dp.getCandles(ticker, days, e3.get())
	#candles = dp.getHistory(ticker, days)
	
	files = [f'./logs/{f}' for f in os.listdir('./logs/')] # if os.path.isfile(f)
	#print(files)
	#os.remove("file_name.txt")
	
	dayData = json.load(open(files[0]))
	#price volume bid ask strike bidsize asksize open_interest option_type delta gamma mid_iv
	
	#res = list(test_dict.keys())[0]    O(n)
	#res = next(iter(test_dict))        O(1)
	#for new_s, new_val in student_name.items():   res=new_s; break;    O(1)
	#first_key = list(student_name.keys())[0]      O(n)
	
	avgs = []

	firstTime = next(iter(dayData))
	price = dayData[firstTime]['price']
	strikes = [strike for strike in dayData[firstTime]['data']]

	#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk
	element = 9 if call == 1 else 11
	for times in dayData:
		price = dayData[times]['price']
		for strike in dayData[times]['data']:
			if strike[0] == strikePrice : avgs.append( strike[element] )
	return avgs
	
#	volumes = []
	for i in range( len( candles ) ) :
		#avgs.append( (candles[i]['high'] + candles[i]['low']) / 2 )
		avgs.append( candles[i]['open'] )
		avgs.append( candles[i]['close'] )
#		volumes.append( candles[i]['volume'] + 1)
#		volumes.append( candles[i]['volume'] + 1)

	return avgs

def drawTickerOnCanvas( ticker, days, color ):
	avgs = prepData( 4360, 1 )
	drawAVGs(avgs, 'green')
	avgs = prepData( 4370, 1 )
	drawAVGs(avgs, 'green')
	avgs = prepData( 4350, 1 )
	drawAVGs(avgs, 'green')
	
	avgs = prepData( 4360, -1 )
	drawAVGs(avgs, 'red')
	avgs = prepData( 4370, -1 )
	drawAVGs(avgs, 'red')
	avgs = prepData( 4350, -1 )
	drawAVGs(avgs, 'red')
	

def drawAVGs(avgs, color):
	global canvas
	#{'open': 450.9499, 'high': 450.9499, 'low': 450.89, 'close': 450.92, 'volume': 2493, 'datetime': 1693612740000}
	
	
	highPrice = max(avgs)
	lowPrice = min(avgs)
	priceRange = highPrice - lowPrice
	scale = IMG_H / priceRange
#	maxVolume = max(volumes)
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

win = Tk()
win.geometry(str(2000 + 5) + "x" + str(IMG_H + 95))

Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, "SPY")

e2 = Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '1')

e3 = Entry(win, width=4)
e3.grid(row=0, column=2, sticky='E')
e3.insert(0, '5')
Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')

Label(win, text="Interval", width=10).grid(row=0, column=3, sticky='W')
Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=4, sticky='E')

canvas = Canvas(win, width=2000, height=IMG_H + 50)
canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
canvas.configure(bg="#000000")

clickButton()
mainloop()