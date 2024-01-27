import datetime
import time
import tkinter as tk
import datapuller as dp
import drawchart as dc
from PIL import Image,ImageTk
import os
import ujson as json #usjon is json written in C

ticker = "SPX"
allFiles = dp.pullLogFileList()
fileList = [x for x in allFiles if ((ticker=='SPX') ^ ('SPY' in x))]
fileList.sort()

lastFileIndex = len( fileList ) -1
fileIndex = lastFileIndex
gex_image, pc_image = None, None

def clickLeftButton():
	global fileIndex
	fileIndex -= 1
	if fileIndex == -1: fileIndex = lastFileIndex
	loadDaysData(setTarget=True)

def clickRightButton():
	global fileIndex
	fileIndex += 1
	if fileIndex > lastFileIndex: fileIndex = 0
	loadDaysData(setTarget=True)

def on_enter(event):
	loadDaysData()
	
def loadDaysData(setTarget=False):
	global gex_image, pc_image
	dte_text.set(str(fileIndex))
	gexData = dp.pullLogFile(fileList[fileIndex])
	day = fileList[fileIndex].replace('-datalog.json','').replace('SPY-','')

	openTime = next(iter(gexData))
	firstStrike = gexData[openTime]['data']
	openPrice = dp.getPrice(ticker, firstStrike)
	strikes = gexData[openTime]['data']

	fileName = dc.drawGEXChart(ticker=ticker, count=40, dte=0, strikes=strikes, price=openPrice, expDate=day, targets=True) 
	gex_image = ImageTk.PhotoImage(Image.open("./" + fileName))
	lGEX.configure(image=gex_image)
	
	targets = dp.findKeyLevels(firstStrike, openPrice, targets=True)
	if setTarget : entry_text.set( f'{targets[0][dp.GEX_STRIKE]}c' )
		
	def findStrike( myStrike, strikeList ):
		return min(strikeList, key=lambda i: abs(i[dp.GEX_STRIKE] - myStrike))
		
	args = entry_text.get().split(' ')[0]
	pcStrike = findStrike( float(args[:-1]), gexData[ next(iter(gexData)) ]['data'] )[dp.GEX_STRIKE]
	pcStrikeCP = dp.GEX_CALL_BID if args[-1] == 'c' else dp.GEX_PUT_BID
	pcStrikeCPVol = dp.GEX_CALL_VOLUME if args[-1] == 'c' else dp.GEX_PUT_VOLUME
	entry_text.set( str(pcStrike) + args[-1] )
	
	candles = []
	lastVolume = 0
	for t in gexData :
		#timeStamp = t.split(":")
		strikes = gexData[t]['data']
		strike = findStrike( pcStrike, strikes )
		if pcStrike != strike[dp.GEX_STRIKE]: print('Boom')
		price = dp.getPrice("SPX", strikes)
		candles.append( (strike[pcStrikeCP], strike[pcStrikeCPVol] - lastVolume, price) )
		lastVolume = strike[pcStrikeCPVol]

	candles2 = []
	lastVolume2 = 0
	if targets :
		pcStrike2 = targets[1][dp.GEX_STRIKE]
		for t in gexData :
			strikes = gexData[t]['data']
			strike = findStrike( pcStrike2, strikes )
			if pcStrike2 != strike[dp.GEX_STRIKE]: print('Boom')
			price = dp.getPrice("SPX", strikes)
			candles2.append( (strike[dp.GEX_PUT_BID], strike[dp.GEX_PUT_VOLUME] - lastVolume, price) )
			lastVolume = strike[dp.GEX_PUT_VOLUME]
	
	global canvas
	canvas.delete("all")
	mostOptionPrice = max( candles, key=lambda i: i[0] )[0]
	mostOptionVolume = max( candles, key=lambda i: i[1] )[1]
	mostOptionPrice2 = max( candles2, key=lambda i: i[0] )[0]
	mostOptionVolume2 = max( candles2, key=lambda i: i[1] )[1]
	#canvas.create_line(0, 3, 750, 3, dash=(1,3), fill="green", width=3)
	mostPrice = max(candles, key=lambda i: i[2])[2]
	minPrice = min(candles, key=lambda i: i[2])[2]
	priceDif = mostPrice - minPrice
	def calcOptionY( y, maxY ): return 750 - ((y / maxY) * 300)
	def calcPriceY( y, maxY ): return 450 - (((y - minPrice) / maxY) * 450)
	
	for x in range(0, len(candles)):
		x1 = (x-1) * 2
		x2 = x * 2
		y1 = calcOptionY(candles[x-1][0], mostOptionPrice)
		y2 = calcOptionY(candles[x][0], mostOptionPrice)
		canvas.create_line(x1, y1, x2, y2, fill="green", width=2)
		
		if targets :
			y1 = calcOptionY(candles2[x-1][0], mostOptionPrice2)
			y2 = calcOptionY(candles2[x][0], mostOptionPrice2)
			canvas.create_line(x1, y1, x2, y2, fill="red", width=2)
		
		#if candles[x][1] < 0 : print(candles[x][1])
		y1 = 850 - ((candles[x][1] / mostOptionVolume) * 100)		
		canvas.create_line(x2 +5, y1, x2 + 5, 851, fill="blue", width=2)

		y1 = calcPriceY(candles[x-1][2], priceDif)
		y2 = calcPriceY(candles[x][2], priceDif)
		#print( priceDif, y1, y2)
		canvas.create_line(x1, y1, x2, y2, fill="yellow", width=2)

	#canvas.create_line(10, 10, 100, 100, dash=(4, 4))
	x = len(candles) * 2
	y = calcPriceY( mostPrice, priceDif )
	canvas.create_text(x, y, text=str(mostPrice), fill="green", anchor="ne" )
	
	y = calcPriceY( minPrice, priceDif )
	canvas.create_text(x, y, text=f'SPX {minPrice}', fill="yellow", anchor="sw" )
	canvas.create_text(x, y, text=f'{targets[0][dp.GEX_STRIKE]}c ${mostOptionPrice} ', fill="green", anchor="ne" )
	canvas.create_text(x, y, text=f' {targets[1][dp.GEX_STRIKE]}p ${mostOptionPrice2}', fill="red", anchor="nw" )
	canvas.create_line(0, y, x, y, fill="yellow", dash=(3,2))
	
	if mostOptionPrice >= 0.2 :	
		y = calcOptionY( 0.2, mostOptionPrice )
		canvas.create_text(x, y, text=f'$0.20 ', fill="green", anchor="se" )
		canvas.create_line(0, y, x, y, fill="green", dash=(3,2))
		
	if mostOptionPrice2 >= 0.2 :	
		y = calcOptionY( 0.2, mostOptionPrice2 )
		canvas.create_text(x, y, text=f' $0.20', fill="red", anchor="sw" )
		canvas.create_line(0, y, x, y, fill="red", dash=(3,2))

	canvas.create_text( x//2, calcOptionY( -0.2, mostOptionPrice ), text=f'{targets[0][dp.GEX_STRIKE]}c and {targets[1][dp.GEX_STRIKE]}p', fill="yellow", anchor="n" )

win = tk.Tk()
win.geometry("1400x1000")
#win.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(win, text="Ticker", width=10, anchor="w").place(x=0, y=0)
e1 = tk.Entry(win, width=6)
e1.place(x=50, y=0)
e1.insert(0, ticker)

dte_text = tk.StringVar()
tk.Label(win, text="Days", width=10, anchor="w").place(x=100, y=0)
e2 = tk.Entry(win, width=4, textvariable=dte_text)
e2.place(x=150, y=0)
dte_text.set(str(fileIndex))

entry_text = tk.StringVar()
e3 = tk.Entry(win, width=8, textvariable=entry_text)
e3.place(x=200, y=0)
entry_text.set('4900c')
e3.bind("<Return>", on_enter)

tk.Button(win, text="<", command=clickLeftButton, width=1).place(x=260, y=0)
tk.Button(win, text=">", command=clickRightButton, width=1).place(x=290, y=0)

lGEX = tk.Label(win)
lGEX.place(x=0, y=30)

#lPriceChart = tk.Label(win)
#lPriceChart.place(x=500, y=30)

canvas = tk.Canvas(win, width=1500, height=900)
canvas.place(x=500, y=30)
canvas.configure(bg="#000000")

loadDaysData(setTarget=True)

tk.mainloop()