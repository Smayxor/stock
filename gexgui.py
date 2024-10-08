import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
import threading
import time
import math
import requests
import ujson as json
import asyncio
import websockets

init = json.load(open('apikey.json'))
BOT_TOKEN = init.get('DISCORD_BOT_2', None)
del init

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
lastFileIndex = len(fileList) - 1
fileIndex = lastFileIndex
fileToday = fileList[fileIndex]
pcData = []
pcY = []
dataIndex = -1

accountBalance = 0
unsettledFunds = 0
openOrders = 'null'
myPositions = 'null'
lblBalance = None
lblOpenOrders = None

pcFloatingX = 0
pcFloatingY = 0
pcFloatingText = None
pcFloatingText2 = None
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
	
	openOrders = dp.getOrders()
	myPositions = dp.getPositions()
	
	#{'order': [
	#{'id': 60524187, 'type': 'limit', 'symbol': 'XSP', 'side': 'buy_to_open', 'quantity': 1.0, 'status': 'canceled', 'duration': 'day', 'price': 0.37, 'avg_fill_price': 0.0, 'exec_quantity': 0.0, 'last_fill_price': 0.0, 'last_fill_quantity': 0.0, 'remaining_quantity': 0.0, 'create_date': '2024-06-27T14:50:12.624Z', 'transaction_date': '2024-06-27T14:51:43.701Z', 'class': 'option', 'option_symbol': 'XSP240627P00547000', 'tag': 'test'}, 
	#{'position': [{'cost_basis': 39.0, 'date_acquired': '2024-06-27T15:03:14.311Z', 'id': 7572248, 'quantity': 1.0, 'symbol': 'XSP240627C00549000'}, {'cost_basis': 5.0, 'date_acquired': '2024-06-27T15:10:15.888Z', 'id': 7572487, 'quantity': 1.0, 'symbol': 'XSP240627C00551000'}]}
	
	orders = []
	orderTxt = None
	if openOrders != 'null' :
		#{'order': {'id': 62661984, 'type': 'limit', 'symbol': 'XSP', 'side': 'buy_to_open', 'quantity': 1.0, 'status': 'filled', 'duration': 'day', 'price': 1.06, 'avg_fill_price': 1.06, 'exec_quantity': 1.0, 'last_fill_price': 1.06, 'last_fill_quantity': 1.0, 'remaining_quantity': 0.0, 'create_date': '2024-07-22T13:59:10.253Z', 'transaction_date': '2024-07-22T13:59:13.094Z', 'class': 'option', 'option_symbol': 'XSP240722C00555000', 'tag': 'test'}}
		
		#[{'id': 62661984, 'type': 'limit', 'symbol': 'XSP', 'side': 'buy_to_open', 'quantity': 1.0, 'status': 'filled', 'duration': 'day', 'price': 1.06, 'avg_fill_price': 1.06, 'exec_quantity': 1.0, 'last_fill_price': 1.06, 'last_fill_quantity': 1.0, 'remaining_quantity': 0.0, 'create_date': '2024-07-22T13:59:10.253Z', 'transaction_date': '2024-07-22T13:59:13.094Z', 'class': 'option', 'option_symbol': 'XSP240722C00555000', 'tag': 'test'}, {'id': 62669560, 'type': 'limit', 'symbol': 'XSP', 'side': 'buy_to_open', 'quantity': 2.0, 'status': 'canceled', 'duration': 'day', 'price': 0.46, 'avg_fill_price': 0.0, 'exec_quantity': 0.0, 'last_fill_price': 0.0, 'last_fill_quantity': 0.0, 'remaining_quantity': 0.0, 'create_date': '2024-07-22T14:12:31.874Z', 'transaction_date': '2024-07-22T14:15:25.549Z', 'class': 'option', 'option_symbol': 'XSP240722C00555000'}, {'id': 62670860, 'type': 'limit', 'symbol': 'XSP', 'side': 'sell_to_close', 'quantity': 1.0, 'status': 'open', 'duration': 'day', 'price': 1.5, 'avg_fill_price': 0.0, 'exec_quantity': 0.0, 'last_fill_price': 0.0, 'last_fill_quantity': 0.0, 'remaining_quantity': 1.0, 'create_date': '2024-07-22T14:14:16.294Z', 'transaction_date': '2024-07-22T14:14:16.365Z', 'class': 'option', 'option_symbol': 'XSP240722C00555000'}]
		

		if not isinstance(openOrders['order'], list):
			openOrders['order'] = [openOrders['order']]
			
		for ord in openOrders['order'] :
			#x = getattr(ord, 'status', 'no')
			# hasattr()
			status = ord.get('status', 'no')
			print(f'Status = {status}' )
			if 'open' in status :
				cp = 'c' if 'C' in ord['option_symbol'] else 'p'
				orderTxt = ord['symbol'] + ' - ' + ord['option_symbol'][-6:-3] + cp
				orders.append( orderTxt )
			elif 'no' in status :
				print(f'Problem Detected - {ord}')
	positions = []
	positionTxt = None
	if myPositions != 'null' :
		pos = myPositions['position']
		print( f'{pos}' )
		cost = float(pos['cost_basis'])
		cp = 'c' if 'C' in pos['symbol'] else 'p'
		positionTxt = pos['symbol'][:3] + ' - ' + pos['symbol'][-6:-3] + cp + ' @ $' + f'{cost}'
		positions.append( ( positionTxt, cost ) )
	
	txt = ""
	if positionTxt == None and orderTxt == None : txt = "No Orders"
	else : 
		if not positionTxt is None : txt = positionTxt 
		if not orderTxt is None : txt += ' - ' + orderTxt
	lblOpenOrders.configure(text=txt)

'''
async def some_IO_func(endpoint):
    resp = await requests.get(endpoint)
    payload = resp.json()
    # do something
    something = payload['header'] ...
    return something'''
def clickButton():
	
	response = requests.post('https://api.tradier.com/v1/markets/events/session', data={}, headers=dp.TRADIER_HEADER)
	json_response = response.json()

	cp = checkCall.get()
	options = dp.getOptionsChain('SPX', 0)
	strikes = dp.getGEX(options[1])
	element = dp.GEX_CALL_ASK if cp == 1 else dp.GEX_PUT_ASK
	symbol = dp.GEX_CALL_SYMBOL if cp == 1 else dp.GEX_PUT_SYMBOL
	
	strike = e3Text.get()[:4] if cp == 1 else e4Text.get()[:4]
	strike = float( strike )
	strike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - strike))
	#strike = min(strikes, key=lambda i: abs(i[element] - 2))
	
	"""
	payload = { 'sessionid': json_response['stream']['sessionid'], 'symbols': f'{strike[symbol]}', 'linebreak': True }
	r = requests.get('https://stream.tradier.com/v1/markets/events', stream=True, params=payload, headers={ 'Accept': 'application/json'})
	
	for line in r.iter_lines():
		if line:
			print(json.loads(line))
	return#{'type': 'quote', 'symbol': 'SPXW240426P05055000', 'bid': 0.35, 'bidsz': 829, 'bidexch': 'C', 'biddate': '1714155461000', 'ask': 0.4, 'asksz': 299, 'askexch': 'C', 'askdate': '1714155463000'}
	"""
	global accountBalance, unsettledFunds, openOrders, myPositions
	cp = checkCall.get()
	strike = e3Text.get()[:4] if cp == 1 else e4Text.get()[:4]
	strike = float( strike )
	print( strike )
	tradePrice = float(optionPrice.get())
	
	if myPositions == "null" and openOrders == "null" :
		options = dp.getOptionsChain('SPX', 0)
		strikes = dp.getGEX(options[1])
		element = dp.GEX_CALL_ASK if cp == 1 else dp.GEX_PUT_ASK
		symbol = dp.GEX_CALL_SYMBOL if cp == 1 else dp.GEX_PUT_SYMBOL
		strike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - strike))
		if tradePrice == 0 : tradePrice = strike[element]
		myCon = dp.placeOptionOrder(strike[symbol], tradePrice, ticker = 'SPX', side='buy_to_open', quantity='1', type='limit', duration='day', tag='gui', preview="true")#
		print( myCon )
		getAccountData(myCon)
	else :
		#getAccountData()
		options = dp.getOptionsChain('SPX', 0)
		strikes = dp.getGEX(options[1])
		element = dp.GEX_CALL_BID if cp == 1 else dp.GEX_PUT_BID
		symbol = dp.GEX_CALL_SYMBOL if cp == 1 else dp.GEX_PUT_SYMBOL

		myCon = [x for x in strikes if x[symbol] == myPositions['position']['symbol']][0]
		if tradePrice == 0 : tradePrice = myCon[element]
		#myCon = dp.placeOptionOrder(myPositions['symbol'], myCon[element], ticker="XSP", side="sell_to_close", quantity='1')
		myCon = dp.placeOptionOrder(myPositions['position']['symbol'], tradePrice, ticker="SPX", side="sell_to_close", quantity='1', type='limit', preview="true")#
		print( myCon )	
		getAccountData(myCon)
	
#Buying Order    {'order': {'status': 'ok', 'commission': 0.39, 'cost': 6.39, 'fees': 0, 'symbol': 'XSP', 'quantity': 1, 'side': 'buy_to_open', 'type': 'limit', 'duration': 'day', 'result': True, 'price': 0.06, 'order_cost': 6.0, 'margin_change': 0.0, 'option_requirement': 0.0, 'request_date': '2024-02-06T17:49:21.748', 'extended_hours': False, 'option_symbol': 'XSP240206C00497000', 'class': 'option', 'strategy': 'option', 'day_trades': 1}}


#{'errors': {'error': 'Sell order is for more shares than your current long position, please review current position quantity along with open orders for security. '}}

#Closing Order    {'order': {'status': 'ok', 'commission': 0.39, 'cost': -1.61, 'fees': 0, 'symbol': 'XSP', 'quantity': 1, 'side': 'sell_to_close', 'type': 'limit', 'duration': 'day', 'result': True, 'price': 0.02, 'order_cost': -2.0, 'margin_change': 0.0, 'option_requirement': 0.0, 'request_date': '2024-02-06T18:20:58.3', 'extended_hours': False, 'option_symbol': 'XSP240206C00497000', 'class': 'option', 'strategy': 'option', 'day_trades': 1}}

#**************** Place an order
#options = dp.getOptionsChain('XSP', 0)
#gexList = dp.getGEX(options[1])
#putStrike = min(gexList, key=lambda i: abs(i[dp.GEX_PUT_ASK] - 0.04))

#myCon = dp.placeOptionOrder(putStrike[dp.GEX_PUT_SYMBOL], 0.04, ticker = 'XSP', side='buy_to_open', quantity='1', type='limit', duration='day', tag='test')
#{'order': {'id': xxx, 'status': 'ok', 'partner_id': 'xxxxxx'}}

#Open positions {'position': {'cost_basis': 4.0, 'date_acquired': '2024-01-25T15:52:41.633Z', 'id': xxxx, 'quantity': 1.0, 'symbol': 'XSP240125P00484000'}}

#***************** Close an order
#myPut = [x for x in gexList if x[dp.GEX_PUT_SYMBOL] == myPosition['symbol']][0]

#myCon = dp.placeOptionOrder(myPosition['symbol'], myPut[dp.GEX_PUT_BID], ticker="XSP", side="sell_to_close", quantity='1')

#{'order': {'id': xxx, 'status': 'ok', 'partner_id': 'xxxxxx'}}
def round_price(price, min_incr): 
	return '{:20,.2f}'.format( price - (price % min_incr) + min_incr ).lstrip()

CALLORPUTA = [dp.GEX_CALL_ASK, dp.GEX_PUT_ASK]
CALLORPUTB = [dp.GEX_CALL_BID, dp.GEX_PUT_BID]
CALLORPUTS = [dp.GEX_CALL_SYMBOL, dp.GEX_PUT_SYMBOL]
testPosition = 0
def placeOrder(callput):
	global testPosition
	options = dp.getOptionsChain('XSP', 0)
	gexList = dp.getGEX(options[1])
	element = CALLORPUTA[callput]

	price = float(optionPrice.get())
	strike = min(gexList, key=lambda i: abs(i[element] - price))
	bid = strike[CALLORPUTB[callput]]
	ask = strike[CALLORPUTA[callput]]
	symbol = strike[CALLORPUTS[callput]]
	midPrice = round_price((bid + ask) / 2, 0.01)
	
	#midPrice = (midPrice * 10) 
	
	if 'XSP' in openOrders : print('Yes')
	if testPosition == 1 : return
	testPosition = 1
	print( "Call" if callput==0 else "Put", strike[dp.GEX_STRIKE], " $", midPrice, symbol )

	try :
		
		myCon = dp.placeOptionOrder(symbol, midPrice, ticker = 'XSP', side='buy_to_open', quantity='1', type='limit', duration='day', tag='test')  #This prints Response Status code

		#{'order': {'id': 60524187, 'status': 'ok', 'partner_id': '30ea5c89-e029-4da3-a179-5867a8006e07'}}
		print(f'New Order Placed - {myCon}')
		#New Order Placed - {'order': {'id': 60530076, 'status': 'ok', 'partner_id': '30ea5c89-e029-4da3-a179-5867a8006e07'}}
		if myCon['order']['status'] == 'ok' : print('Order placed')
		getAccountData()#myCon)
		#myCon2 = dp.placeOptionOrder(symbol, midPrice * 2, ticker="XSP", side="sell_to_close", quantity='1')  # Can not place a close order until filled without OTOCO
	except Exception as error:
		print(f'Trade failure - {error}')
		
	#New Order Placed - {'order': {'status': 'ok', 'commission': 0.39, 'cost': 8.39, 'fees': 0, 'symbol': 'XSP', 'quantity': 1, 'side': 'buy_to_open', 'type': 'limit', 'duration': 'day', 'result': True, 'price': 0.08, 'order_cost': 8.0, 'margin_change': 0.0, 'option_requirement': 0.0, 'request_date': '2024-08-07T16:59:22.727', 'extended_hours': False, 'option_symbol': 'XSP240807C00533000', 'class': 'option', 'strategy': 'option', 'day_trades': 1}}

#import signals as sig
def triggerReset():
	global canvas, ticker, blnReset, strikeCanvasImage, pc_tk_image, pc_image, fileToday
	global pcData, pcY, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingDot, pcFloatingText2, ticker
	blnReset = False
	ticker = editTicker.get().upper()
	
	try:
		gexData = dp.pullLogFile(fileToday, cachedData=False)
		firstTime = min( gexData.keys(), key=lambda i: abs(631 - float(i)))
		gexList = gexData[firstTime]
		exp = fileToday.replace("-0dte-datalog.json", "")
		price = dp.getPrice(ticker, gexList)   #Mega important!!!   If Price returns 0, dp.getPrice would  use a LastPrice for faulty return
		#if price == 0 : print( firstTime , ' - ', gexList[0])
		image = dc.drawGEXChart(ticker, 40, dte=0, strikes=gexList, price=price, expDate=exp + ' ' + firstTime, RAM=True) #function needs optional parameter to pass gexdata in
		resize_image = image.resize((340,605))
		tk_image = ImageTk.PhotoImage(resize_image)
		canvas.configure(image=tk_image)
		canvas.image = tk_image
		minute = 630
		if fileIndex != lastFileIndex :
			for minute in gexData:
				if float(minute) >= 640 :
					gexList = gexData[minute]
					break
					
		initVChart( gexList, ticker )
	
		price = dp.getPrice(ticker=ticker, strikes=gexList)

		tmp = dc.drawPriceChart(ticker, fileToday, gexData, [e3.get(), e4.get()], includePrices = True, RAM=True, deadprice=float(deadPrice.get()), timeMinute=minute, startTime=startTime.get(), stopTime=stopTime.get())
		pcData = tmp[1]
		pcY = tmp[2]
		filename = tmp[0]
		#if 'error' in filename: return
		pc_image = filename#Image.open("./" + filename)
		pc_tk_image = ImageTk.PhotoImage(pc_image)
		strikecanvas.delete('all')
		strikeCanvasImage = strikecanvas.create_image(0,0,image=pc_tk_image, anchor=tk.NW)
		pcFloatingText = strikecanvas.create_text( 515, 100, fill='blue', text=e3.get(), anchor="w", tag='float', font=("Helvetica", 16) )
		pcFloatingText2 = strikecanvas.create_text( -515, 100, fill='blue', text=e3.get(), anchor="w", tag='float', font=("Helvetica", 16) )
		pcFloatingDot = strikecanvas.create_line(500, 100, 515, 115, fill='blue', width = 3, dash=(1,3))
		strikecanvas.bind("<Motion>", strikecanvas_on_mouse_move)
		setPCFloat(-1,-1)
		
		canvas.bind('<Button-1>', on_gex_strike_click)
	except Exception as error:
		print("An exception occurred:", error)

"""response = json.load(open('crash.json'))
options = response.get('options', dict({'a': 123})).get('option', None)
gex = dp.getGEX(options)
tmpPrice = dp.getPrice("SPX", gex)
crashGEX = dp.shrinkToCount(gex, tmpPrice, 50)"""

def timerThread():
	global pcData, pcY, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingText2, pcFloatingDot, strikeCanvasImage, pc_tk_image, pc_image
	global dataIndex, fileIndex, fileList, fileToday, ticker
	errorLine = 0
	if blnReset: triggerReset()
	errorLine = 1
	dte = dteText.get()
	errorLine = 2
	if not dte.isnumeric(): dte = 0
	else : dte = int(dte)
	errorLine = 3
	if dte != fileIndex : 
		fileIndex = dte
		fileToday = fileList[fileIndex]
		triggerReset()
		return
	errorLine = 4
		
	newTicker = editTicker.get()
	errorLine = 5
	if newTicker == "GME" and ticker == "SPX" :
		ticker = newTicker
		fileList = fileListGME
		fileIndex = 0
		fileToday = fileListGME[fileIndex]
		dteText.set('0')
		triggerReset()
		print(f'GME Switch ')
		return
	errorLine = 6
	
	try:
		gexData = dp.pullLogFile(fileToday, cachedData=fileIndex!=lastFileIndex)
		if fileIndex==lastFileIndex : gexData = gexData
		errorLine = 7
		
		#print(f'{fileToday} {fileIndex}={lastFileIndex} --> {len(gexData)}')
		
		minute = 0
		st = float(startTime.get())
		times = [x for x in list(gexData.keys()) if float(x) > st]
		lastTimes = len(times) - 1
		errorLine = 8
		if fileIndex==lastFileIndex :
			minute = times[-1]
			gexList = gexData[minute]
			price = dp.getPrice(ticker, gexList, 0)
			cPrice = float(callPrice.get())
			pPrice = float(putPrice.get())
			if price < cPrice :
				placeOrder(0)
			if price > pPrice :
				placeOrder(1)
		errorLine = 9
		if dataIndex == -1 or dataIndex > lastTimes: dataIndex = lastTimes
		errorLine = 10
		minute = times[dataIndex]  #Sets the Minute to a time mouse is hovering
		minute = str( minute )
		errorLine = 11
		gexList = gexData[minute]
		errorLine = 12
		
		#**************************************************************************************************
		newStrikes = None
		deltaVolumeTime = int(sliderValue.get())
		if  0 < deltaVolumeTime < dataIndex:
			prevIndex = dataIndex - deltaVolumeTime
			prevMinute = times[prevIndex]
			prevGEX = gexData[prevMinute]
			newStrikes = []
			for strike, prevStrike in zip(gexList, prevGEX):
				if strike[dp.GEX_STRIKE] != prevStrike[dp.GEX_STRIKE] :
					print('Error comparing strikes')
					break
				tmpStrike = [strike[dp.GEX_STRIKE], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "None", "None"]
				tmpStrike[dp.GEX_CALL_BID] = strike[dp.GEX_CALL_BID]
				tmpStrike[dp.GEX_PUT_BID] = strike[dp.GEX_PUT_BID]
				tmpStrike[dp.GEX_CALL_VOLUME] = strike[dp.GEX_CALL_VOLUME] - prevStrike[dp.GEX_CALL_VOLUME]
				tmpStrike[dp.GEX_PUT_VOLUME] = strike[dp.GEX_PUT_VOLUME] - prevStrike[dp.GEX_PUT_VOLUME]
				tmpStrike[dp.GEX_CALL_OI] = strike[dp.GEX_CALL_OI] #- prevStrike[dp.GEX_CALL_OI]
				tmpStrike[dp.GEX_PUT_OI] = strike[dp.GEX_PUT_OI] #- prevStrike[dp.GEX_PUT_OI]
				#tmpStrike[dp.GEX_CALL_GEX] = strike[dp.GEX_CALL_GEX] - prevStrike[dp.GEX_CALL_GEX]
				#tmpStrike[dp.GEX_PUT_GEX] = strike[dp.GEX_PUT_GEX] + prevStrike[dp.GEX_PUT_GEX]
				newStrikes.append( tmpStrike )
		
		#***************************************************************************************************
		errorLine = 13
		
		refreshVCanvas(strikes=gexList if newStrikes==None else newStrikes)
		errorLine = 131
		price = dp.getPrice(ticker, gexList )
		errorLine = 132
		win.title( f'Price ${price}')
		errorLine = 14
		
		minute = float(times[dataIndex])
		firstTime = min( gexData.keys(), key=lambda i: abs(minute - float(i)))
		gexList = gexData[firstTime]
		exp = fileToday.replace("-0dte-datalog.json", "")
		image = dc.drawGEXChart(ticker, 40, dte=0, chartType=0, strikes=gexList, price=price, expDate=exp + ' ' + firstTime, RAM=True)
		resize_image = image.resize((340,605))
		tk_image = ImageTk.PhotoImage(resize_image)
		canvas.configure(image=tk_image)
		canvas.image = tk_image
		
		errorLine = 15
		tmp = dc.drawPriceChart(ticker, fileToday, gexData, [e3.get(), e4.get()], includePrices = True, RAM=True, deadprice=float(deadPrice.get()), timeMinute=minute, startTime=startTime.get(), stopTime=stopTime.get())
		
		errorLine = 16
		pcData = tmp[1]
		pcY = tmp[2]
		filename = tmp[0]
		pc_image = filename# Image.open("./" + filename)
		pc_tk_image = ImageTk.PhotoImage(pc_image)
		strikecanvas.itemconfig(strikeCanvasImage, image=pc_tk_image)

	except Exception as error:
		print( 'Timerthread Error ', error , errorLine)

def strikecanvas_on_mouse_move(event):	setPCFloat(event.x, event.y)
		
def setPCFloat(x, y):
	global pcData, pcY, pcFloatingX, pcFloatingY, pcFloatingText, pcFloatingText2, pcFloatingDot, dataIndex
	
	if pcFloatingText == None : return
	all = 'all' in e3Text.get()
	tops = 0
	mouseY = y
	ypcFT2 = -500
	txtFT2 = ""
	if x > -1:
		firstPCData = pcData[0]
		mostX = len(firstPCData) - 1
		if x > mostX : x = mostX
		y2 = pcY[0][x]
		txt = f'  ${round((firstPCData[x]), 2)} '
		if all : 
			y2 = y
			y = pcY[0][x] - 5
		else : 
			y = pcY[0][x]
			y2 = y + 5
			tops = 1
			if len(pcData) == 2:
				firstPCData = pcData[1]
				y2 = pcY[1][x]
				txtFT2 = f'  ${round((firstPCData[x]), 2)} '
				#txt += f'\n  ${round((firstPCData[x]), 2)} '
		
		strikecanvas.coords(pcFloatingDot, x, y, x, y2)
		if len(pcData) == 1 : y = mouseY
		strikecanvas.coords(pcFloatingText, x, y+25)
		strikecanvas.itemconfig(pcFloatingText, text=txt)
		strikecanvas.coords(pcFloatingText2, x, y2-25)
		strikecanvas.itemconfig(pcFloatingText2, text=txtFT2)
		
	strikecanvas.itemconfig(pcFloatingText, anchor="e" if x > 1200 else "w")
	strikecanvas.itemconfig(pcFloatingText2, anchor="e" if x > 1200 else "w")
	dataIndex = x#len(pcData)

def on_strike_click(event):
	global vcStrikes
	if event.y < 73:
		if event.x < 50 : e3Text.set('spx')
		elif event.x > 115 : e4Text.set('spx')
		else : e3Text.set('all')
	else :
		index = (605 - event.y) // 14
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
				
		cbCall.configure(text=text)
	timerThread()

def on_gex_strike_click(event):
	global vcStrikes
	if event.y < 65: 
		e3Text.set('all')
	else :
		index = int( (594 - event.y) / 12.6 )
		endText = 'c' if event.x < 243 else 'p'
		text = str(vcStrikes[index].Strike).split('.')[0] + endText
		if endText == 'c' : 
			e3Text.set(text)
			checkCall.set(1)
		else: 
			e4Text.set(text)
			checkCall.set(0)
			if e3Text.get() == 'all' :
				e3Text.set( str(vcStrikes[index].Strike).split('.')[0] + 'c' )
				
		cbCall.configure(text=text)
	timerThread()	

def initVChart(strikes, ticker):
	global vPrice, vCallGEX, vPutGEX, vcStrikes
	vcanvas.delete('all')
	del vcStrikes
	vcStrikes = []
	firstStrike = strikes[0]
	price = dp.getPrice("SPX", strikes) 
	vPrice = price
	strikes = dp.shrinkToCount(strikes, price, 40)
	y = 590
	half_size = 6
	for strike in strikes:
		txt = str(round((strike[0]), 2))
		canvasStrikeText = vcanvas.create_text( 70, y, fill='white', text=txt, tag='widget', anchor="n" )
		#vcanvas.tag_bind('widget', '<Button-1>', on_strike_click)
		canvasCall = vcanvas.create_rectangle(0, y, 50, y +half_size+half_size, fill='green', tag='widget')
		canvasCallVol = vcanvas.create_rectangle(0, y, 100, y+half_size, fill='blue', tag='widget')

		canvasPut = vcanvas.create_rectangle(90, y, 150, y + half_size + half_size, fill='red', tag='widget')
		canvasPutVol = vcanvas.create_rectangle(90, y, 150, y + half_size, fill='yellow', tag='widget')
		
		canvasCallPrice = vcanvas.create_text(3, y, fill='red', text=str(round((strike[dp.GEX_CALL_BID]), 2)), tag='widget', anchor="nw")
		canvasPutPrice = vcanvas.create_text(130, y, fill='green', text=str(round((strike[dp.GEX_PUT_BID]), 2)), tag='widget', anchor="nw")
		
		vcStrikes.append( CanvasItem(strike[dp.GEX_STRIKE], y, canvasCall, canvasPut, canvasCallVol, canvasPutVol, canvasCallPrice, canvasPutPrice, canvasStrikeText) )
		y -= 14
		
	allTarget = vcanvas.create_text( 70, 7, fill='white', text='  SPX    -    Show-All    -   SPX', tag='widget' )
	vcanvas.tag_bind('widget', '<Button-1>', on_strike_click)
	refreshVCanvas(strikes = strikes)
	
#def convertY( val ):	return SCANVAS_HEIGHT - ((val - lowPrice) * scale)

	
def refreshVCanvas(strikes = None):  #VCanvas is  GEX Volume chart on right side
	calcVals = []
	for strike in strikes:
		coi = strike[dp.GEX_CALL_OI]
		poi = strike[dp.GEX_PUT_OI]
		cv = strike[dp.GEX_CALL_VOLUME]
		pv = strike[dp.GEX_PUT_VOLUME]
		
		coiv = coi + cv
		poiv = poi + pv
		
		#coi *= cv #Exponential Volume reading for Gamma Skew
		#poi *= pv
		
		cb = strike[dp.GEX_CALL_BID]
		pb = strike[dp.GEX_PUT_BID]
		calcVals.append( (strike[dp.GEX_STRIKE], coi, poi, cv, pv, cb, pb, coiv, poiv) )

	maxCallOI = max(calcVals, key=lambda i: i[1])[1]
	#maxPutOI = abs( min(calcVals, key=lambda i: i[2])[2] )
	maxPutOI = max(calcVals, key=lambda i: i[2])[2]
	maxCallPutOI = max( (maxCallOI, maxPutOI) )
	maxCallVolume = max(calcVals, key=lambda i: i[3])[3]
	#maxPutVolume = abs( min(calcVals, key=lambda i: i[4])[4] )
	maxPutVolume = max(calcVals, key=lambda i: i[4])[4]
	maxCallPutVolume = max( (maxCallVolume, maxPutVolume) )
	maxCallPutOI = max( [maxCallPutOI, maxCallPutVolume] )
	maxCOIV = max( calcVals, key=lambda i: i[7])[7]
	maxPOIV = max( calcVals, key=lambda i: i[8])[8]
	maxSize = 50
	
	half_size = 6
	for vcItem in vcStrikes:
		strike = next((x for x in calcVals if x[0] == vcItem.Strike), None)
		if strike == None: continue
		
		cStrike = 0
		if strike[7] * 1.20 >= maxCOIV : cStrike = 1
		if strike[8] * 1.20 >= maxPOIV : cStrike += 2
		VOL_COLORS = ["white", "green", "red", "blue"]
		vcanvas.itemconfig(vcItem.strikeText, fill=VOL_COLORS[cStrike])

		callSize = (strike[1] / maxCallPutOI) * maxSize
		putSize = (strike[2] / maxCallPutOI) * maxSize
		vcanvas.coords(vcItem.callCanvas, 50-callSize, vcItem.Y, 50, vcItem.Y + half_size + half_size)
		vcanvas.coords(vcItem.putCanvas, 90, vcItem.Y, 90 + putSize, vcItem.Y + half_size + half_size)

		callSize = (strike[3] / maxCallPutOI) * maxSize
		putSize = (strike[4] / maxCallPutOI) * maxSize
		vcanvas.coords(vcItem.callVolCanvas, 50-callSize, vcItem.Y, 50, vcItem.Y + half_size)
		vcanvas.coords(vcItem.putVolCanvas, 90, vcItem.Y, 90 + putSize, vcItem.Y + half_size)

		vcanvas.itemconfig(vcItem.callPriceText, text=str(round((strike[5]), 2)))
		vcanvas.itemconfig(vcItem.putPriceText, text=str(round((strike[6]), 2)))

		vcanvas.itemconfig(vcItem.strikeText, text=str(round((strike[0]), 2)))


def clickLeftButton():
	global fileIndex, fileList, fileToday
	fileIndex -= 1
	if fileIndex == -1: fileIndex = lastFileIndex
	dteText.set( str(fileIndex) )
	fileToday = fileList[fileIndex]
	triggerReset()

def clickRightButton():
	global fileIndex, fileList, fileToday, lastFileIndex
	fileIndex += 1
	if fileIndex > lastFileIndex: fileIndex = 0
	dteText.set( str(fileIndex) )
	fileToday = fileList[fileIndex]
	triggerReset()
	
def on_closing():
	global blnRun, timer
	blnRun = False
	timer.cancel()
	win.destroy()

win = tk.Tk()
#win.geometry(str(2200) + "x" + str(IMG_H + 45))
width, height = 2200, IMG_H + 45
win.geometry('%dx%d+%d+%d' % (width, height, 0, 50))
win.protocol("WM_DELETE_WINDOW", on_closing)

editTicker = tk.Entry(win, width=6)
editTicker.insert(0, ticker)
editTicker.place(x=2, y=0)

lblTicker = tk.Label(win, text="Ticker", width=10, anchor="w")
lblTicker.place(x=30, y=0)

dteText = tk.StringVar() 
e2 = tk.Entry(win, width=8, textvariable=dteText)
e2.place(x=80, y=0)
e2.insert(0, str(fileIndex))

lblDays = tk.Label(win, text="Days", width=10, anchor="w")
lblDays.place(x=100, y=0)

tk.Button(win, text="<", command=clickLeftButton, width=1).place(x=130, y=0)
tk.Button(win, text=">", command=clickRightButton, width=1).place(x=150, y=0)

deadPrice = tk.Spinbox(win, width=4, wrap=True, values=(0.30, 0.25, 0.20, 0.15, -0.1, 0.6, 0.55, 0.5, 0.45, 0.40))#from_=10, to=50)
deadPrice.place(x=200, y=0)

e3Text = tk.StringVar() 
e3Text.set("all") 
e3 = tk.Entry(win, width=8, textvariable=e3Text)
e3.place(x=300, y=0)

e4Text = tk.StringVar() 
e4Text.set("4850p")
e4 = tk.Entry(win, width=8, textvariable=e4Text)
e4.place(x=355, y=0)

sliderValue = tk.DoubleVar() 
s1 = tk.Scale( win, variable = sliderValue, from_ = 0, to = 100, orient = tk.HORIZONTAL, length=500)
s1.place(x=650, y=0)

startTime = tk.StringVar() 
startTime.set("-1000") 
eStartTime = tk.Entry(win, width=8, textvariable=startTime)
eStartTime.place(x=800, y=0)

stopTime = tk.StringVar() 
stopTime.set("1300") 
eStopTime = tk.Entry(win, width=8, textvariable=stopTime)
eStopTime.place(x=850, y=0)

btnFetch = tk.Button(win, text="Buy/Sell", command=clickButton, width=8)
btnFetch.place(x=0, y=700)

checkCall = tk.IntVar()
cbCall = tk.Checkbutton(win, text='Call', variable=checkCall, onvalue=1, offvalue=0)#, command=print_selection)
cbCall.place(x=0, y=670)
checkCall.set(1)

lblBalance = tk.Label(win, text="Account Balance $", width=30, anchor="w")
lblBalance.place(x = 150, y = 650)

lblOpenOrders = tk.Label(win, text=f'Open orders - {openOrders}', width=300, anchor="w")
lblOpenOrders.place(x = 150, y = 670)

lblOptionPrice = tk.Label(win, text=f'Trade Price $', width=12, anchor="w")
lblOptionPrice.place(x = 0, y =650)
optionPrice = tk.StringVar() 
optionPrice.set("0.10")
e5 = tk.Entry(win, width=4, textvariable=optionPrice)
e5.place(x=75, y=650)

getAccountData()

canvas = tk.Label()
canvas.place(x=0, y=40)

vcanvas = tk.Canvas()
vcanvas.place(x=340, y=40)
vcanvas.configure(width=150, height=605, bg='black')

strikecanvas = tk.Canvas(win,width= 1400, height=705, bg='black')
strikecanvas.place(x=492, y=40)
#strikecanvas.configure(width= 2600, height= 2800)

lblCallPrice = tk.Label(win, text=f'Buy Call @ $', width=12, anchor="w")
lblCallPrice.place(x = 150, y =690)
callPrice = tk.StringVar() 
callPrice.set("0000")
e6 = tk.Entry(win, width=6, textvariable=callPrice)
e6.place(x=225, y=690)

lblPutPrice = tk.Label(win, text=f'Buy Put  @ $', width=12, anchor="w")
lblPutPrice.place(x = 150, y =710)
putPrice = tk.StringVar() 
putPrice.set("9999")
e7 = tk.Entry(win, width=6, textvariable=putPrice)
e7.place(x=225, y=710)



timer = dp.RepeatTimer(5, timerThread, daemon=True)
timer.start()
timerThread()






if BOT_TOKEN != None :

	from discord.ext import tasks
	import discord
	from discord.ext import commands
	from discord import app_commands
	
	#import "C:\Users\hmset\Desktop\tradier\gobcog-master\adventure.py" as Adventure
	#sys.path.insert(0, 'C:\Users\hmset\Desktop\tradier\gobcog-master\adventure.py')
	
	#import sys
	#sys.path.insert(0, './gobcog-master/adventure')
	#import adventure
	
	class MyBotHelp(commands.MinimalHelpCommand):
		async def send_pages(self):
			strHelp = """No Help"""
			destination = self.get_destination()
			for page in self.paginator.pages:
				await destination.send(strHelp)
	bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyBotHelp(), sync_commands=True)

	@bot.command(name="bot")
	async def command_bot(ctx, *args): 
		arg = args[0]	
		if 'all' in arg : 
			e3Text.set('all')
			return
		if len(args) != 1 : await ctx.send( f'One command at a time' )
		if len(arg) != 5 : await ctx.send( f'Strike + c or p example 5425c - {len(arg)}' )
		isCall = 'c' in arg
		isPut = 'p' in arg
		if isCall == False and isPut == False : 
			await ctx.send( f'Call {isCall} - Put {isPut}' )
			return
		try :
			strike = int( arg[:4] )
		except:
			await ctx.send( f'Couldn\'t decode strike {arg[:4]}' )
			return
	
		if isCall :
			e3Text.set( str(strike) + 'c' )
			checkCall.set(1)
		if isPut :
			e4Text.set( str(strike) + 'p' )
			checkCall.set(0)
			
	@bot.command(name="clone")
	async def command_clone(ctx, *args): 	
		# ECONONMY = 804191163610824735
		# Adeventure = 1064534371144572928
		
		guild = ctx.message.guild
		#jsonChannel = { "name": "adventure", "id": "1064534371144572928"  }
		#await guild.create_text_channel("adventure")
		
		
		channels = await guild.fetch_channels()
		category = discord.utils.get(channels, name='economy')
		await category.create_text_channel('adventure')
		
		#await guild.create_text_channel('adventure', category=category)

	@bot.command(name="stop")
	async def command_stop(ctx, *args): 
		await bot.close()
		await bot.logout()
		exit(0)

	def run_bot(): bot.run(BOT_TOKEN)
	thread = threading.Thread(target=run_bot)
	thread.start()

tk.mainloop()