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

accountBalance = 0
unsettledFunds = 0
openOrders = 'null'
myPositions = 'null'
lblBalance = None
lblOpenOrders = None

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

def getAccountData(newCon = ""):
	global accountBalance, unsettledFunds, openOrders, myPositions
	balance = dp.getAccountBalance()['cash']
	#{'cash_available': 115.3, 'sweep': 0, 'unsettled_funds': 0}
	accountBalance = balance['cash_available']
	unsettledFunds = balance['unsettled_funds']
	lblBalance.config(text = f'Account Balance ${accountBalance}')
	
	openOrders = dp.getOrders() if newCon == "" else newCon
	if newCon == "" : myPositions = dp.getPositions()
	#openOrders = dp.getOrders()
	lblOpenOrders.configure(text=f'Open orders - {openOrders} - Positions - {myPositions}')

def clickButton():
	global accountBalance, unsettledFunds, openOrders, myPositions
	cp = checkCall.get()
	strike = e3Text.get()[:3] if cp == 1 else e4Text.get()[:3]
	strike = float( strike )
	tradePrice = float(optionPrice.get())

	if myPositions == "null" and openOrders == "null" :
		options = dp.getOptionsChain('XSP', 0)
		strikes = dp.getGEX(options[1])
		element = dp.GEX_CALL_ASK if cp == 1 else dp.GEX_PUT_ASK
		symbol = dp.GEX_CALL_SYMBOL if cp == 1 else dp.GEX_PUT_SYMBOL
		strike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - strike))
		if tradePrice == 0 : tradePrice = strike[element]
		myCon = dp.placeOptionOrder(strike[symbol], tradePrice, ticker = 'XSP', side='buy_to_open', quantity='1', type='limit', duration='day', tag='gui')#, preview="true"
		print( myCon )
		getAccountData(myCon)
	else :
		#getAccountData()
		options = dp.getOptionsChain('XSP', 0)
		strikes = dp.getGEX(options[1])
		element = dp.GEX_CALL_BID if cp == 1 else dp.GEX_PUT_BID
		symbol = dp.GEX_CALL_SYMBOL if cp == 1 else dp.GEX_PUT_SYMBOL

		myCon = [x for x in strikes if x[symbol] == myPositions['position']['symbol']][0]
		if tradePrice == 0 : tradePrice = myCon[element]
		#myCon = dp.placeOptionOrder(myPositions['symbol'], myCon[element], ticker="XSP", side="sell_to_close", quantity='1')
		myCon = dp.placeOptionOrder(myPositions['position']['symbol'], tradePrice, ticker="XSP", side="sell_to_close", quantity='1', type='limit')#, preview="true"
		print( myCon )	
		getAccountData(myCon)
	
#Buying Order    {'order': {'status': 'ok', 'commission': 0.39, 'cost': 6.39, 'fees': 0, 'symbol': 'XSP', 'quantity': 1, 'side': 'buy_to_open', 'type': 'limit', 'duration': 'day', 'result': True, 'price': 0.06, 'order_cost': 6.0, 'margin_change': 0.0, 'option_requirement': 0.0, 'request_date': '2024-02-06T17:49:21.748', 'extended_hours': False, 'option_symbol': 'XSP240206C00497000', 'class': 'option', 'strategy': 'option', 'day_trades': 1}}


#{'errors': {'error': 'Sell order is for more shares than your current long position, please review current position quantity along with open orders for security. '}}

#Closing Order    {'order': {'status': 'ok', 'commission': 0.39, 'cost': -1.61, 'fees': 0, 'symbol': 'XSP', 'quantity': 1, 'side': 'sell_to_close', 'type': 'limit', 'duration': 'day', 'result': True, 'price': 0.02, 'order_cost': -2.0, 'margin_change': 0.0, 'option_requirement': 0.0, 'request_date': '2024-02-06T18:20:58.3', 'extended_hours': False, 'option_symbol': 'XSP240206C00497000', 'class': 'option', 'strategy': 'option', 'day_trades': 1}}

#**************** Place an order
#options = dp.getOptionsChain('XSP', 0)
#gexList = dp.getGEX(options[1])
#putStrike = min(gexList, key=lambda i: abs(i[dp.GEX_PUT_ASK] - 0.04))
#print( putStrike )
#myCon = dp.placeOptionOrder(putStrike[dp.GEX_PUT_SYMBOL], 0.04, ticker = 'XSP', side='buy_to_open', quantity='1', type='limit', duration='day', tag='test')
#{'order': {'id': xxx, 'status': 'ok', 'partner_id': 'xxxxxx'}}
#print(  myCon )
#Open positions {'position': {'cost_basis': 4.0, 'date_acquired': '2024-01-25T15:52:41.633Z', 'id': xxxx, 'quantity': 1.0, 'symbol': 'XSP240125P00484000'}}

#***************** Close an order
#myPut = [x for x in gexList if x[dp.GEX_PUT_SYMBOL] == myPosition['symbol']][0]
#print(f'Close order {myPut}')
#myCon = dp.placeOptionOrder(myPosition['symbol'], myPut[dp.GEX_PUT_BID], ticker="XSP", side="sell_to_close", quantity='1')
#print( myCon )
#{'order': {'id': xxx, 'status': 'ok', 'partner_id': 'xxxxxx'}}

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
		strikecanvas.delete('all')
		strikeCanvasImage = strikecanvas.create_image(0,0,image=pc_tk_image, anchor=tk.NW)
		pcFloatingText = strikecanvas.create_text( 515, 100, fill='blue', text=e3.get(), anchor="w", tag='float', font=("Helvetica", 16) )
		pcFloatingDot = strikecanvas.create_oval(500, 100, 515, 115, fill='blue', width = 3)
		strikecanvas.bind("<Motion>", strikecanvas_on_mouse_move)
		setPCFloat(-1,-1)
	except Exception as error:
		print("An exception occurred:", error)

def timerThread():
	global pcData, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingDot, strikeCanvasImage, pc_tk_image, pc_image
	if blnReset: triggerReset()
	dte = e2.get()
	if not dte.isnumeric(): dte = 0
	try:
		gexData = dp.pullLogFile(fileToday)
		gexList = list(gexData.values())[-1]
		#print( gexList ) #***********************************************************
		
		refreshVCanvas(strikes=gexList)

		price = dp.getPrice( "SPX", gexList, 0 )
		win.title( f'Price ${price}')

		tmp = dc.drawPriceChart("SPX", fileToday, gexData, [e3.get(), e4.get()], includePrices = True)
		pcData = tmp[1]
		filename = tmp[0]
		if 'error' in filename: return
		pc_image = Image.open("./" + filename)
		pc_tk_image = ImageTk.PhotoImage(pc_image)
		strikecanvas.itemconfig(strikeCanvasImage, image=pc_tk_image)

	except Exception as error:
		print( 'Error ', error )

def strikecanvas_on_mouse_move(event):	setPCFloat(event.x, event.y)
		
def setPCFloat(x, y):
	global pcData, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingDot
	
	if pcFloatingText == None : return
	minPrice, maxPrice, difPrice = 0, 0, 0

	all = 'all' in e3Text.get()
	tops = 0 if (all) or (y < 300) else 1

	def spxY( val ): return 537 - (((val - minPrice) / difPrice) * 500)
	def convertY( val ): return 537 - ((val / maxPrice) * 250) - 252 + (tops * 250)
		
	if x > -1:
		firstPCData = pcData[tops]
		mostX = len(firstPCData) - 1
		if x > mostX : x = mostX
		maxPrice = max( firstPCData )
		minPrice = min( firstPCData )
		difPrice = maxPrice - minPrice
		
		if all : y = spxY( firstPCData[x] )
		else : y = convertY( firstPCData[x] )
		
		strikecanvas.coords(pcFloatingText, x, y)
		strikecanvas.itemconfig(pcFloatingText, text=f'  ${round((firstPCData[x]), 2)}')
		strikecanvas.coords(pcFloatingDot, x-3, y-3, x+3, y+3)
		
	strikecanvas.itemconfig(pcFloatingText, anchor="e" if x > 1200 else "w")

def on_strike_click(event):
	global vcStrikes
	if event.y < 73: 
		e3Text.set('all')
	else :
		index = (685 - event.y) // 20
		endText = 'c' if event.x < 67 else 'p'
		text = str(vcStrikes[index].Strike).split('.')[0] + endText
		if endText == 'c' : 
			e3Text.set(text)
			checkCall.set(1)
		else: 
			e4Text.set(text)
			checkCall.set(0)
			if e3Text.get() == 'all' :
				e3Text.set( str(vcStrikes[index].Strike).split('.')[0] + 'c' )
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
e3.place(x=300, y=0)

e4Text = tk.StringVar() 
e4Text.set("4850p")
e4 = tk.Entry(win, width=8, textvariable=e4Text)
e4.place(x=355, y=0)

btnFetch = tk.Button(win, text="Buy/Sell", command=clickButton, width=8)
btnFetch.place(x=550, y=0)

checkCall = tk.IntVar()
cbCall = tk.Checkbutton(win, text='Call',variable=checkCall, onvalue=1, offvalue=0)#, command=print_selection)
cbCall.place(x=620, y=0)
checkCall.set(1)

lblBalance = tk.Label(win, text="Account Balance $", width=30, anchor="w")
lblBalance.place(x = 670, y = 0)

lblOpenOrders = tk.Label(win, text=f'Open orders - {openOrders}', width=300, anchor="w")
lblOpenOrders.place(x = 820, y = 0)

lblOptionPrice = tk.Label(win, text=f'Trade Price $', width=12, anchor="w")
lblOptionPrice.place(x = 400, y = 0)
optionPrice = tk.StringVar() 
optionPrice.set("0.10")
e5 = tk.Entry(win, width=4, textvariable=optionPrice)
e5.place(x=475, y=0)

getAccountData()

canvas = tk.Label()
canvas.place(x=0, y=40)

vcanvas = tk.Canvas()
vcanvas.place(x=400, y=40)
vcanvas.configure(width=150, height=700, bg='black')

strikecanvas = tk.Canvas(win,width= 1500, height=550, bg='black')
strikecanvas.place(x=552, y=40)
#strikecanvas.configure(width= 2600, height= 2800)

timer = dp.RepeatTimer(5, timerThread, daemon=True)
timer.start()
timerThread()

tk.mainloop()
"""
rectLayer = Image.new("RGBA", self.backgroundImage.size)
rectDraw = ImageDraw.Draw(rectLayer)
rectDraw.rectangle([start, end], fill="#00000080")
rectDraw.line((x0, y0, x1, y0, x1, y1, x0, y1, x0, y0), fill="#ffffff", width=1)
print("drawing: ", time() - t)
t = time()

displayImage = Image.alpha_composite(self.backgroundImage, self.linesLayer)
displayImage.alpha_composite(rectLayer, (0, 0), (0, 0))
print("image blend: ", time() - t)
t = time()

self.photoImage = ImageTk.PhotoImage(displayImage)"""