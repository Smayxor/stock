import datetime
import json #usjon is json written in C
import tkinter as tk
from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont, Image,ImageTk
import PIL.Image as PILImg
import requests
from threading import Timer

TIMER_INTERVAL = 2000  # Time in millisecond to update
init = json.load(open('apikey.json'))
API_KEY = init.get('apikey', None)
if API_KEY is None :
	API_KEY = init.get('TRADIER_ACCESS_CODE', None)
	
if API_KEY is None :
	print('dude API Key not found')
	exit(0)
TRADIER_HEADER = {'Authorization': f'Bearer {API_KEY}', 'Accept': 'application/json'}	
GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_CALL_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL, GEX_PUT_IV, GEX_CALL_DELTA, GEX_PUT_DELTA, GEX_CALL_GAMMA, GEX_PUT_GAMMA = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24

class RepeatTimer(Timer): #Deprecated - Using built in TKinter function now
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		self.stopped = self.stoppedEvent
		
	def stoppedEvent(self):
		print(f'Stop Event {datetime.datetime.today()}')
		
	def run(self):#, daemon=True):
		#self.interval = 60
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)

def sessionSetValues(ticker, expDate):
	sess = requests.Session()
	param = {'symbol': f'{ticker}', 'expiration': f'{expDate}', 'greeks': 'true'}
	req = requests.Request('GET',  'https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER)
	prepped = sess.prepare_request(req)
	return (sess, req, prepped)
	
async def sessionGetOptionsChain(sess, req, prepped):
	response = sess.send( prepped, timeout=5 )
	if not response.status_code == requests.codes.ok :
		print( 'getOptionsChain ', response.status_code, response.content )
		return None
	if not response.headers.get('Content-Type').startswith('application/json') : 
		print( f'Not JSON - {response.headers} - {response.content}' )
		return None
	response = response.json()
	#***************************************************** In the event we get an unexpected packet **********************************************
	#with open(f'{CACHE_PATH}crash.json', 'w') as f:
	#	json.dump(response, f)
	#*********************************************************************************************************************************************
	options = response.get('options', dict({'a': 123})).get('option', None)
	if options is None :
		print(f'Unexpected response in getOptionsChain - {response}')
		return None
	return options
	
def getOptionsChain(ticker, dte, date=None):
	#print( f'Fetching {dte} on {ticker}')
	if date == None :
		expDate = getExpirationDate(ticker, dte)
	else : expDate = date
	param = {'symbol': f'{ticker}', 'expiration': f'{expDate}', 'greeks': 'true'}
	
	response = None
	try :
		response = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER, timeout=5 )
	except Exception as error:
		print(f'getOptionsChain {error}')
		return None
	
	if not response.status_code == requests.codes.ok :
		print( 'getOptionsChain ', response.status_code, response.content )
		return None
	if not response.headers.get('Content-Type').startswith('application/json') : 
		print( f'Not JSON - {response.headers} - {response.content}' )
		return None
	response = response.json()
	#***************************************************** In the event we get an unexpected packet **********************************************
	#with open(f'{CACHE_PATH}crash.json', 'w') as f:
	#	json.dump(response, f)
	#*********************************************************************************************************************************************
	options = response.get('options', dict({'a': 123})).get('option', None)
	if options is None :
		print(f'Unexpected response in getOptionsChain - {response}')
		return None
	return (expDate, options)
	
def getExpirations(ticker):
	param = {'symbol': f'{ticker}', 'includeAllRoots': 'true', 'strikes': 'false'}   #'strikes': 'true'}
	response = requests.get('https://api.tradier.com/v1/markets/options/expirations', params=param, headers=TRADIER_HEADER)
	if response.status_code != 200 : print( 'getExpirations ', response.status_code, response.content )
	return response.json()['expirations']['date']

def shrinkToCount(strikes, price, count, remove=False):
	firstStrike, lastStrike = strikes[0], strikes[-1]
	result = sorted( sorted( strikes, key=lambda strike: abs(strike[GEX_STRIKE] - price) )[:count], key=lambda strike: strike[GEX_STRIKE] )
	if remove : return result
	if firstStrike[GEX_STRIKE] != result[0][GEX_STRIKE] : result.insert( 0, firstStrike )
	if lastStrike[GEX_STRIKE] != result[-1][GEX_STRIKE] : result.append( lastStrike )
	return result
	
	
def getQuote(ticker):
	ticker = ticker.upper()
	param = {'symbols': 'SPY', 'greeks': 'false'} if ticker == 'SPX' else {'symbols': f'{ticker}', 'greeks': 'false'}
	#param = {'symbols': f'{ticker}', 'greeks': 'false'}
	result = requests.get('https://api.tradier.com/v1/markets/quotes', params=param, headers=TRADIER_HEADER).json()['quotes']['quote']['ask']
	"""{'quotes': {'quote': {'symbol': 'SPY', 'description': 'SPDR S&P 500', 'exch': 'P', 'type': 'etf', 'last': 469.33, 'change': 0.0, 
	'volume': 308790, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 470.74, 'ask': 470.75, 'change_percentage': 0.0, 
	'average_volume': 83226262, 'last_volume': 0, 'trade_date': 1702688400003, 'prevclose': 469.33, 'week_52_high': 473.73, 'week_52_low': 374.77, 
	'bidsize': 1, 'bidexch': 'Q', 'bid_date': 1702906169000, 'asksize': 32, 'askexch': 'P', 'ask_date': 1702906170000, 'root_symbols': 'SPY'}}}"""
	if ticker == 'SPX' : result *= SPY2SPXRatio
	return result

lastPriceFromGetPrice = 0
def getPrice(ticker, strikes = None, ba=0):
	global lastPriceFromGetPrice
	
	firstStrike = strikes[0]
	lastStrike = strikes[-1]

	cs = firstStrike[GEX_STRIKE]
	ps = lastStrike[GEX_STRIKE]
	cb = firstStrike[GEX_CALL_BID]
	pb = lastStrike[GEX_PUT_BID]
	ca = firstStrike[GEX_CALL_ASK]
	pa = lastStrike[GEX_PUT_ASK]
	cp, pp = 0, 0
	
	if ba == 0:
		cp = cs + ((cb + ca) / 2)
		pp = ps - ((pb + pa) / 2)
	elif ba == 1:
		cp = cs + cb
		return cp
	elif ba == 2:
		pp = ps - pb
		return pp	
	elif ba == -1:
		cp = cs + ca
		return cp
	elif ba == -2:
		pp = ps - pa
		return pp

	if cb == 0 and pb == 0 : return None
	
	price = cp if cp<pp and firstStrike[GEX_CALL_BID] != 0 else pp
	#price = (cp + pp) / 2
	#if price < 5000 :
	#	print( cp, cs, cb, ca )
	#	print( pp, ps, pb, pa )

	#blnUp = lastPriceFromGetPrice > price
	#lastPriceFromGetPrice = price
	#price = cs + (cb if blnUp else ca)
	return price
	
def getGEX(options):  #An increase in IV hints at Retail Buying = High IV is Handicapping
	index = 0
	strikes = []
	def findIndex( strike ): #loop from end of list, confirm we are using correct index
		index = len(strikes) - 1
		while strikes[index][GEX_STRIKE] != strike: index -= 1
		return index
	#print( options )
	foundSymbols = []
	for option in options:
		if not option['root_symbol'] in foundSymbols : foundSymbols.append(option['root_symbol'])
		if option['root_symbol'] == 'SPX' : continue  #get rid of monthlies
		#if index == 0: print( option )#['root_symbol'] )
		strike = option['strike'] 
		call = 1 if option['option_type'] == 'call' else -1
		gamma = 0 
		iv = 0
		if option['greeks'] is not None:
			gamma = option['greeks']['gamma']
			iv = option['greeks']['mid_iv']
			delta = option['greeks']['delta']
			#thetaXrho = f'{round(option['greeks']['theta'], 2)}x{round(option['greeks']['rho'], 2)}'
		volume = option['volume']
		oi = option['open_interest'] 

		#if chartType == 1: # WTF Delete this soon ********
		#	oi = volume #For Volume charts
		#	gex = oi * call
		#else:
		gex = oi * gamma * call
		#exDate = option['expiration_date']
		bid = option['bid']
		ask = option['ask']
		bidSize = option['bidsize']
		askSize = option['asksize']
		symbol = option['symbol']
		#if strike == 4350 : print( option )
		if (len(strikes) == 0) or (strikes[index][0] != strike): #fast, assumes strikes are in order
			strikes.append( [strike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "None", "None", 0, 0, 0, 0, 0] ) 
			index = findIndex(strike) # always make sure we're on the right strike index
		#GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_CALL_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL, GEX_PUT_IV, GEX_CALL_DELTA, GEX_PUT_DELTA, GEX_CALL_GAMMA, GEX_PUT_GAMMA
		tmp = strikes[index]
		if call == 1: 
			tmp[GEX_STRIKE], tmp[GEX_CALL_IV], tmp[GEX_CALL_BID], tmp[GEX_CALL_ASK], tmp[GEX_CALL_VOLUME], tmp[GEX_CALL_BID_SIZE], tmp[GEX_CALL_ASK_SIZE], tmp[GEX_CALL_DELTA], tmp[GEX_CALL_GAMMA] = strike, iv, bid, ask, volume, bidSize, askSize, delta, gamma
			tmp[GEX_CALL_GEX] += gex  #We can have multiple root symbols SPX and SPXW
			tmp[GEX_CALL_OI]+= oi
			tmp[GEX_CALL_SYMBOL] = symbol
			#tmp[GEX_CALL_THETA] = thetaXrho
		else: 
			tmp[GEX_STRIKE], tmp[GEX_PUT_IV], tmp[GEX_PUT_BID], tmp[GEX_PUT_ASK], tmp[GEX_PUT_VOLUME], tmp[GEX_PUT_BID_SIZE], tmp[GEX_PUT_ASK_SIZE], tmp[GEX_PUT_DELTA], tmp[GEX_PUT_GAMMA] = strike, iv, bid, ask, volume, bidSize, askSize, delta, gamma
			tmp[GEX_PUT_GEX] += gex
			tmp[GEX_PUT_OI]+= oi
			tmp[GEX_PUT_SYMBOL] = symbol
			#tmp[GEX_PUT_THETA] = thetaXrho

	for index in range( len(strikes) ):
		strikes[index][GEX_TOTAL_GEX] = strikes[index][GEX_CALL_GEX] + strikes[index][GEX_PUT_GEX]
		strikes[index][GEX_TOTAL_OI] = strikes[index][GEX_CALL_OI] + strikes[index][GEX_PUT_OI]
		strikes[index] = [0 if i is None else i for i in strikes[index]]#filter out any suprises
		strikes[index] = [round(i, 10) if isinstance(i, float) else i for i in strikes[index]]
		#if index == 90: print( strikes[index] )
		#[3810.0, 2.0440077796170993e-11, 570, -2.227444375223762e-12, 51, 2.2667522171394755e-11, 519, 0.0, 1221.3, 1222.0, 0.0, 0.05, 0, 1, 1, 0, 0, 1831, 'SPXW240216C03810000', 'SPXW240216P03810000']
		#[3810.0, 0.0, 570, -0.0, 51, 0.0, 519, 0.0, 1222.8, 1223.3, 0.0, 0.05, 0, 1, 1, 0, 0, 1831, 'SPXW240216C03810000', 'SPXW240216P03810000']

	#print( foundSymbols )
	return strikes

class OptionPriceTracker():
	def __init__(self, strikes, isCall, Strike, SpotPrice=0, strikeDelta=None):
		self.Strike = Strike
		self.IsCall = isCall
		self.Letter = 'c' if isCall else 'p'
		self.VolElement = GEX_CALL_VOLUME if isCall else GEX_PUT_VOLUME
		self.BidElement = GEX_CALL_BID if isCall else GEX_PUT_BID
		self.AskElement = GEX_CALL_ASK if isCall else GEX_PUT_ASK
		self.OIElement = GEX_CALL_OI if isCall else GEX_PUT_OI
		self.GammaElement = GEX_CALL_GAMMA if isCall else GEX_PUT_GAMMA
		self.DeltaElement = GEX_CALL_DELTA if isCall else GEX_PUT_DELTA
		self.Index = -1
		for i in range(len(strikes)):
			if strikes[i][GEX_STRIKE] == Strike: 
				self.Index = i
				break
		if self.Index == -1:
			#print(f'OptionPriceTracker Init Error Strike not found {Strike}')
			return None
		strike = strikes[self.Index]
		self.Bid = strike[self.BidElement]
		self.Ask = strike[self.AskElement]
		self.Volume = strike[self.VolElement]
		self.OI = strike[self.OIElement]
		self.Gamma = strike[self.GammaElement]
		self.Delta = strike[self.DeltaElement]
		if not strikeDelta is None :
			self.Volume -= strikeDelta[self.Index][self.VolElement]
		self.GEX = self.Gamma * self.Volume * 100 * SpotPrice * 0.01 * (1 if self.IsCall else -1)
		#gamma * volume * spot price * 100 * spot price * -.01 for putside
		
	def genOPT(strikes, SpotPrice, low=0, high=999999, strikeDelta=None):
		Options = []
		for strike in strikes:
			val = strike[GEX_STRIKE]
			if not (low <= val <= high) : continue
			c = OptionPriceTracker(strikes, True, val, SpotPrice=SpotPrice, strikeDelta=strikeDelta)
			p = OptionPriceTracker(strikes, False, val, SpotPrice=SpotPrice, strikeDelta=strikeDelta)
			if (c.Index == -1) or (p.Index == -1) : continue
			Options.append(c)
			Options.append(p)
		return Options

resetDTEDate = datetime.date.today()  #To reduce requests per minute from broker, we store a list of all tickers every day, and their ExpirationDates
tickerDTEList = {}
def getExpirationDate(ticker, dte):
	global resetDTEDate, tickerDTEList
	today = datetime.date.today()

	if resetDTEDate != today :
		resetDTEDate = today
		tickerDTEList = {}
	dates = None
	if ticker in tickerDTEList : 
		dates = tickerDTEList[ticker]
	else: 
		dates = getExpirations( ticker )
		tickerDTEList[ticker] = dates

	while True:  #We want to find something.  hopefully the correct DTE
		result = str(today + datetime.timedelta(days=int(dte))).split(":")[0]
		#print( f'DTE result {result}' )
		if result in dates:
			return result #dates[dteIndex]
			break
		dte += 1
	return result

def getToday():
	tempo = datetime.datetime.today()# + datetime.timedelta(1) #For testing purposes
	minute = (tempo.hour * 100) + tempo.minute + (tempo.second * 0.01)
	if minute > 1800 :
		tempo = tempo + datetime.timedelta(1)
		minute = minute - 2400
	tomorrow = tempo + datetime.timedelta(1)
	todaysDate = f'{tempo.year}-{tempo.month:02d}-{tempo.day:02d}'
	return (todaysDate, minute, tempo.month, tomorrow)
	
dates = getExpirations( 'SPX' )
dteIndex = dates.index( getToday()[0] )
RecordDate = dates[dteIndex]	
print( 'Fetching SPX data for - ',RecordDate )
#Sess, Req, Prepped = sessionSetValues('SPX', RecordDate)   # This is only for cool people

optionsData = None
def timerThread():
	global optionsData
	optionsData = getGEX(getOptionsChain('SPX', 0)[1])
	
FONT_SIZE = 22
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic")
pc_image, pc_tk_image, strikeCanvasImage = None, None, None
def updateCanvas():
	global pc_image, pc_tk_image, strikeCanvasImage, optionsData
	win.after(TIMER_INTERVAL, updateCanvas)
	if optionsData is None : return
	
	SpotPrice = getPrice('SPX', optionsData)
	strikes = shrinkToCount(optionsData, SpotPrice, 60, remove=True)
	options  = OptionPriceTracker.genOPT(strikes, SpotPrice)
	IMG_W = 1800
	IMG_H = 1000
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	
	x = 400
	y = 0
	maxVolume = max( options, key=lambda o: o.Volume ).Volume
	maxOI = max( options, key=lambda o: o.OI ).OI
	maxGEX = abs(max( options, key=lambda o: abs(o.GEX) ).GEX)
	BAR_WIDTH = 100
	for i in range(0, len(options), 2) :
		call, put = options[i], options[i+1]

		draw.text((x,y), text=f'{call.Strike}', fill='yellow', font=font, anchor='la')
		val = (call.GEX / maxGEX) * BAR_WIDTH
		try :	draw.rectangle([x-val-5,y,x-5,y+15], fill='green', outline='green')
		except: pass
		val = (put.GEX / maxGEX) * BAR_WIDTH
		try: draw.rectangle([x+80,y,x+80-val,y+15], fill='red', outline='red')  # PUT GEX is Negative so we SUBTRACT it
		except: pass
		
		y += 20
		
	#draw.line([x, y, x, y + 4], fill=color, width=1)
	#draw.text((x,y), text=f'{y}', fill='yellow', font=font, anchor='la')
	#draw.rectangle([x,y,w,h], fill=color, outline=border)
	
	#if RAM : return img
	pc_image = img
	pc_tk_image = ImageTk.PhotoImage(pc_image)
	#pc_image = filename#Image.open("./" + filename)
	#pc_tk_image = ImageTk.PhotoImage(pc_image)
	if not strikeCanvasImage is None: strikecanvas.delete(strikeCanvasImage)
	strikeCanvasImage = strikecanvas.create_image(0,0,image=pc_tk_image, anchor=tk.NW, tag='widget')
	
def on_strike_click(event):
	pass
	
def on_closing():
	win.destroy()
	
win = tk.Tk()
#win.geometry(str(2200) + "x" + str(IMG_H + 45))
width, height = 1800, 1000
win.geometry('%dx%d+%d+%d' % (width, height, 0, 50))
win.protocol("WM_DELETE_WINDOW", on_closing)

strikecanvas = tk.Canvas(win,width= 1800, height=1000, bg='black')
strikecanvas.place(x=0, y=00)
#strikecanvas.configure(width= 2600, height= 2800)
strikecanvas.bind('<Button-1>', on_strike_click, add=None)


timer = RepeatTimer(5, timerThread, daemon=True) #5 seconds
timer.start()
timerThread()

win.after(500, updateCanvas)
tk.mainloop()
