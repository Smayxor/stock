import datetime
import ujson as json #usjon is json written in C
from threading import Timer
import requests
import os
import heapq
init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_ACCOUNT_ID = init['TRADIER_ACCOUNT_ID']
del init
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
FIBS = [-1, -0.786, -0.618, -0.5, -0.382, -0.236, 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
RANGE_FIBS = range(len(FIBS))
SPY2SPXRatio = 0 # No longer used
INDICES = ['SPX', 'VIX', 'XSP', 'SOX']

GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19

"""
firstData = {}
firstData[1] = "aaa"

appendData = {}
appendData[123] = "abc"

with open("./logs/test.json", 'a+') as f:
	f.seek(0,2)
	f.write( json.dumps(firstData) )
	
with open("./logs/test.json", 'rb+') as f:
	f.seek(-1,os.SEEK_END)	#f.truncate()
	f.write( json.dumps(appendData).replace('{', ',').encode() )

appendData[123] = "ddd"
appendData[456] = "eee"
with open("./logs/test.json", 'rb+') as f:
	f.seek(-1,os.SEEK_END)	#f.truncate()
	f.write( json.dumps(appendData).replace('{', ',').encode() )
"""

class RepeatTimer(Timer):
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		
	def run(self):#, daemon=True):
		#self.interval = 60
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)

def findKeyLevels(strikes, price, targets=False):
	if targets :
		"""
		callContractList = [x for x in strikes if x[GEX_STRIKE] > price and x[GEX_CALL_BID] > 0.3]
		putContractList = [x for x in strikes if x[GEX_STRIKE] < price and x[GEX_PUT_BID] > 0.3]

		mostCallGEX = heapq.nlargest( 3, callContractList, key = lambda i: i[GEX_CALL_GEX])
		mostCallOI = heapq.nlargest( 3, callContractList, key = lambda i: i[GEX_CALL_OI])
		mostCallVolume = heapq.nlargest( 3, callContractList, key = lambda i: i[GEX_CALL_VOLUME])

		mostPutGEX = heapq.nlargest( 3, putContractList, key = lambda i: -i[GEX_PUT_GEX])
		mostPutOI = heapq.nlargest( 3, putContractList, key = lambda i: i[GEX_PUT_OI])
		mostPutVolume = heapq.nlargest( 3, putContractList, key = lambda i: i[GEX_PUT_VOLUME])

		#callContractList = mostCallOI + [i for i in mostCallVolume if i not in mostCallOI]
		#putContractList = mostPutOI + [i for i in mostPutVolume if i not in mostPutOI]
		"""
		
		#mostCallOI = max(strikes, key=lambda i: i[GEX_CALL_OI])[GEX_CALL_OI] * 0.6
		#mostPutOI = max(strikes, key=lambda i: i[GEX_PUT_OI])[GEX_PUT_OI] * 0.6
		
		callContractList = heapq.nlargest( 5, strikes, key = lambda i: i[GEX_CALL_GEX])# if i[GEX_CALL_OI] > mostCallOI else 0)
		putContractList = heapq.nlargest( 5, strikes, key = lambda i: -i[GEX_PUT_GEX])# if i[GEX_PUT_OI] > mostPutOI else 0)

		#mostCallOI = max(strikes, key=lambda i: i[GEX_CALL_OI])
		#mostPutOI = max(strikes, key=lambda i: i[GEX_PUT_OI])
		callTargets = [x[GEX_STRIKE] for x in callContractList]
		putTargets = [x[GEX_STRIKE] for x in putContractList]
		targets = sorted(callTargets + [x for x in putTargets if x not in callTargets])
		
		x = 0
		lastTarget = len(targets)
		while x < lastTarget:
			y = x+1
			while y < lastTarget:
				#print( f'Testing {targets[x]} - {targets[y]}' )
				if abs(targets[x] - targets[y]) == 5:
					#print( f'Removing {targets[y]}' )
					del targets[y]
					lastTarget -= 1
				else: y += 1	
			x += 1

		return (callContractList, putContractList, targets)
	else :
		keyLevels = []
		def checkIfExists( strike ):
			if strike not in keyLevels: keyLevels.append( strike )
		priceLower = price - (price % 65) - 10
		priceUpper = priceLower + 100

		nearStrikes = [x for x in strikes if priceLower < x[GEX_STRIKE] < priceUpper]
		VALS_TO_CHECK = [GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_OI, GEX_PUT_OI]
		n = 2 if targets else 3
		for val in VALS_TO_CHECK:
			#sorted(zip(score, name), reverse=True)[:3]
			#heapq.nlargest(n, iterable, key=None)
			most3 = heapq.nlargest(n, nearStrikes, key=lambda i: i[val])
			for biggy in most3: checkIfExists( biggy[GEX_STRIKE] )
		return keyLevels

def findPeaksAndValleys( prices ):
	lenavgs = len( prices )
	highs = []
	lows = []
	last = prices[0]
	high = 0
	low = 0
	def checkNextHigh(index):
		#last = index + 30 if index + 30 < lenavgs else lenavgs
		last = index + 30
		if last > lenavgs : return False
		for i in range(index, last):
			if prices[i] > prices[index] : return False
		return True
	def checkNextLow(index):
		#last = index + 30 if index + 30 < lenavgs else lenavgs
		last = index + 30
		if last > lenavgs : return False
		for i in range(index, last):
			if prices[i] < prices[index] : return False
		return True

	for i in range( 1, lenavgs ) :
		if prices[i] > prices[high] and checkNextHigh(i):
			highs.append(i)
			high = i
			low = i
		elif prices[i] < prices[low] and checkNextLow(i):
			lows.append(i)
			low = i
			high = i
		else:
			pass
	return (lows, highs)
	

def getMarketHoursToday():
	#{'clock': {'date': '2023-11-12', 'description': 'Market is closed', 'state': 'closed', 'timestamp': 1699778863, 'next_change': '07:00', 'next_state': 'premarket'}}
	return requests.get('https://api.tradier.com/v1/markets/clock', params={'delayed': 'false'}, headers=TRADIER_HEADER).json()['clock']

def getExpirations(ticker):
	param = {'symbol': f'{ticker}', 'includeAllRoots': 'true', 'strikes': 'false'}   #'strikes': 'true'}
	return requests.get('https://api.tradier.com/v1/markets/options/expirations', params=param, headers=TRADIER_HEADER).json()['expirations']['date']

def getExpirationDate(ticker, dte):
	today = datetime.date.today()
	dates = getExpirations( ticker )
	while True:
		result = str(today + datetime.timedelta(days=int(dte))).split(":")[0]
		if result in dates: break
		dte += 1
	return result

def getOptionsChain(ticker, dte):
	#print( f'Fetching {dte} on {ticker}')
	expDate = getExpirationDate(ticker, dte)
	param = {'symbol': f'{ticker}', 'expiration': f'{expDate}', 'greeks': 'true'}
	response = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER )
	#print( response.status_code )
	options = response.json()['options']['option']
	
	return (expDate, options)

def getMultipleDTEOptionChain(ticker, days):
	exps = getExpirations(ticker)
	#if today == exps[0] : exps.pop(0)
	exps = exps[:days]
	days = []
	for exp in exps:
		param = {'symbol': f'{ticker}', 'expiration': f'{exp}', 'greeks': 'true'}
		options = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER ).json()['options']['option']
		gex = getGEX( options )
		days.append( (exp, gex) )
	return days

#{'symbol': 'SPY231030C00499000', 'description': 'SPY Oct 30 2023 $499.00 Call', 'exch': 'Z', 'type': 'option', 'last': 0.01, 'change': 0.0, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.01, 'underlying': 'SPY', 'strike': 499.0, 'greeks': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 2e-05, 'rho': 0.0, 'phi': 0.0, 'bid_iv': 0.0, 'mid_iv': 0.716638, 'ask_iv': 0.716638, 'smv_vol': 0.16, 'updated_at': '2023-10-27 20:00:01'}, 'change_percentage': 0.0, 'average_volume': 0, 'last_volume': 11, 'trade_date': 1697812231388, 'prevclose': 0.01, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'Q', 'bid_date': 1698437676000, 'asksize': 5608, 'askexch': 'X', 'ask_date': 1698437691000, 'open_interest': 36, 'contract_size': 100, 'expiration_date': '2023-10-30', 'expiration_type': 'weeklys', 'option_type': 'call', 'root_symbol': 'SPY'}
#{'symbol': 'SPXW240216P00200000', 'description': 'SPXW Feb 16 2024 $200.00 Put', 'exch': 'C', 'type': 'option', 'last': None, 'change': None, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.05, 'underlying': 'SPX', 'strike': 200.0, 'greeks': {'delta': -2.25e-14, 'gamma': -3.2575160249757252e-15, 'theta': 2.236129405855236e-11, 'vega': 2.0000060368178682e-05, 'rho': 0.0, 'phi': 0.0, 'bid_iv': 0.0, 'mid_iv': 0.0, 'ask_iv': 0.0, 'smv_vol': 0.42, 'updated_at': '2024-02-15 20:59:59'}, 'change_percentage': None, 'average_volume': 0, 'last_volume': 0, 'trade_date': 0, 'prevclose': None, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'C', 'bid_date': 1708093802000, 'asksize': 1067, 'askexch': 'C', 'ask_date': 1708095327000, 'open_interest': 9, 'contract_size': 100, 'expiration_date': '2024-02-16', 'expiration_type': 'standard', 'option_type': 'put', 'root_symbol': 'SPXW'}
#{'symbol': 'SPX240216P00400000', 'description': 'SPX Feb 16 2024 $400.00 Put', 'exch': 'C', 'type': 'option', 'last': 0.05, 'change': 0.0, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.15, 'underlying': 'SPX', 'strike': 400.0, 'greeks': {'delta': -1.338e-13, 'gamma': -1.9037189917344295e-14, 'theta': -0.19774195063757755, 'vega': 2.0000113384843898e-05, 'rho': 0.0005479309221920519, 'phi': -0.006882528396090493, 'bid_iv': 0.0, 'mid_iv': 0.0, 'ask_iv': 0.0, 'smv_vol': 1.134, 'updated_at': '2024-02-15 20:59:59'}, 'change_percentage': 0.0, 'average_volume': 0, 'last_volume': 1, 'trade_date': 1705501802447, 'prevclose': 0.05, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'C', 'bid_date': 1708032417000, 'asksize': 0, 'askexch': 'C', 'ask_date': 1708045200000, 'open_interest': 1080, 'contract_size': 100, 'expiration_date': '2024-02-16', 'expiration_type': 'standard', 'option_type': 'put', 'root_symbol': 'SPX'}
def getGEX(options, chartType = 0):  #New test code
	index = 0
	strikes = []
	def findIndex( strike ): #loop from end of list, confirm we are using correct index
		index = len(strikes) - 1
		while strikes[index][GEX_STRIKE] != strike: index -= 1
		return index
	
	for option in options:
		if option['root_symbol'] == 'SPX' : continue  #get rid of monthlies
		#if index == 0: print( option )#['root_symbol'] )
		strike = option['strike'] 
		call = 1 if option['option_type'] == 'call' else -1
		gamma = 0 
		iv = 0
		if option['greeks'] is not None:
			gamma = option['greeks']['gamma']
			iv = option['greeks']['mid_iv']
		volume = option['volume']
		oi = option['open_interest'] 

		if chartType == 1: 
			oi = volume #For Volume charts
			gex = oi * call
		else:
			gex = oi * gamma * call
		#exDate = option['expiration_date']
		bid = option['bid']
		ask = option['ask']
		bidSize = option['bidsize']
		askSize = option['asksize']
		symbol = option['symbol']
		#if strike == 4350 : print( option )
		if (len(strikes) == 0) or (strikes[index][0] != strike): #fast, assumes strikes are in order
			strikes.append( [strike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "None", "None"] ) 
			index = findIndex(strike) # always make sure we're on the right strike index
		#GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL
		tmp = strikes[index]
		if call == 1: 
			tmp[GEX_STRIKE], tmp[GEX_IV], tmp[GEX_CALL_BID], tmp[GEX_CALL_ASK], tmp[GEX_CALL_VOLUME], tmp[GEX_CALL_BID_SIZE], tmp[GEX_CALL_ASK_SIZE] = strike, iv, bid, ask, volume, bidSize, askSize
			tmp[GEX_CALL_GEX] += gex  #We can have multiple root symbols SPX and SPXW
			tmp[GEX_CALL_OI]+= oi
			tmp[GEX_CALL_SYMBOL] = symbol
		else: 
			tmp[GEX_STRIKE], tmp[GEX_IV], tmp[GEX_PUT_BID], tmp[GEX_PUT_ASK], tmp[GEX_PUT_VOLUME], tmp[GEX_PUT_BID_SIZE], tmp[GEX_PUT_ASK_SIZE] = strike, iv, bid, ask, volume, bidSize, askSize
			tmp[GEX_PUT_GEX] += gex
			tmp[GEX_PUT_OI]+= oi
			tmp[GEX_PUT_SYMBOL] = symbol

	for index in range( len(strikes) ):
		strikes[index][GEX_TOTAL_GEX] = strikes[index][GEX_CALL_GEX] + strikes[index][GEX_PUT_GEX]
		strikes[index][GEX_TOTAL_OI] = strikes[index][GEX_CALL_OI] + strikes[index][GEX_PUT_OI]
		strikes[index] = [0 if i is None else i for i in strikes[index]]#filter out any suprises
		strikes[index] = [round(i, 10) if isinstance(i, float) else i for i in strikes[index]]
		#if index == 90: print( strikes[index] )
		#[3810.0, 2.0440077796170993e-11, 570, -2.227444375223762e-12, 51, 2.2667522171394755e-11, 519, 0.0, 1221.3, 1222.0, 0.0, 0.05, 0, 1, 1, 0, 0, 1831, 'SPXW240216C03810000', 'SPXW240216P03810000']
		#[3810.0, 0.0, 570, -0.0, 51, 0.0, 519, 0.0, 1222.8, 1223.3, 0.0, 0.05, 0, 1, 1, 0, 0, 1831, 'SPXW240216C03810000', 'SPXW240216P03810000']

	return strikes

def calcZeroGEX(data): #def add(a, b): return (b[0], a[1] + b[1]) #cumsum = list(accumulate(data, add)) #return min(cumsum, key=lambda i: i[1])[0]
	newList = [(data[0][0], data[0][1])]
	for x in range( 1, len( data ) -1 ): newList.append( (data[x][0], newList[x-1][1] + data[x][1]) )
	return min(newList, key=lambda i: i[1])[0]
	
def calcMaxPain(strikes):
	maxP = {}
	maxPain = next(iter(strikes))[0]
	maxP[maxPain] = 0
	for i in strikes :
		dollars = 0
		for j in strikes : 
#			if i[0] > j[0] : dollars += abs(j[0] - i[0]) * j[4]
#			if i[0] < j[0] : dollars += abs(j[0] - i[0]) * j[6]
#			if i[0] == j[0] : dollars += j[4] + j[6]
			dollars += abs(j[0] - i[0]) * (j[4] if i[0] > j[0] else j[6])
		maxP[i[0]] = dollars
		if maxP[i[0]] < maxP[maxPain] : maxPain = i[0]
#	print( maxPain )
	
	return maxPain

def shrinkToCount(strikes, price, count):
	firstStrike, lastStrike = strikes[0], strikes[-1]
	result = sorted( sorted( strikes, key=lambda strike: abs(strike[GEX_STRIKE] - price) )[:count], key=lambda strike: strike[GEX_STRIKE] )
	if firstStrike[GEX_STRIKE] != result[0][GEX_STRIKE] : result.insert( 0, firstStrike )
	if lastStrike[GEX_STRIKE] != result[-1][GEX_STRIKE] : result.append( lastStrike )
	return result
	""" Old code
	atmStrike = 0.0
	dist = 99999
	for x in strikes:  #Locate the most ATM Strike
		thisDist = abs(x[0] - price)
		if thisDist < dist:
			atmStrike = x[0]
			dist = thisDist
	i = len(strikes) -1
	while (len(strikes) > count) and i > first:# -1:  #Saving first strike for the purpose of detecting Price later
		matches = 0
		dist = abs(atmStrike - strikes[i][0])
		for j in strikes: 
			if abs(atmStrike - j[0]) < dist : matches += 1 
		if matches > count: strikes.pop(i) 
		i -= 1
	return strikes """

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

def getPrice(ticker, strikes = None, dte = "now"):
	if ticker in INDICES and strikes != None:
		#*************************************************************************************************************
		# Needs to correctly factor in value from DTE
		#**************************************************************************************************************
		"""if 'now' in dte: dte = str(datetime.datetime.now()).split(' ')[0]
		end_date = datetime.datetime.strptime(dte, '%Y-%m-%d')
		num_days = (end_date - datetime.datetime.now()).days + 1
		num_weekends = num_days // 7
		dte = num_days - (num_weekends * 2)
		"""
		price = strikes[0][GEX_STRIKE] + ((strikes[0][GEX_CALL_BID] + strikes[0][GEX_CALL_ASK]) / 2)
		"""
		1dte = 1.40 over
		23dte = 0.15 under
		77dtee = 19.80 under
		"""
		#print( price, dte )
		
	else: price = getQuote(ticker)
	return price

def getATR(ticker_name):  #SPX needs to grab SPY and convert
	today = str(datetime.date.today()).split(":")[0]
	#today = str(datetime.date.today() - datetime.timedelta(days=1)).split(":")[0]
	atr_start = str(datetime.date.today() - datetime.timedelta(days=21)).split(":")[0]

	param = {'symbol': f'{ticker_name}', 'interval': 'daily', 'start': f'{atr_start}', 'end': f'{today}', 'session_filter': 'all'}
	candles = requests.get('https://api.tradier.com/v1/markets/history', params=param, headers=TRADIER_HEADER).json()['history']['day']
	previousClose = 0.0
	lastCandle = len(candles) - 2
	x = lastCandle
	atr = 0
	while x > lastCandle - 14:
		candle = candles[x]
		x -= 1
		previousClose = candle['close']
		high = candle['high']
		low = candle['low']
		upper = abs( high - previousClose )
		lower = abs( low - previousClose )
		both = abs( high - low )
		atr += max( [upper, lower, both] )

	previousClose = candles[lastCandle]['close']
	atr = atr / 14
	return (atr, getATRLevels(previousClose, atr), previousClose)

def getATRLevels(price, atr): #	global FIBS, RANGE_FIBS
	result = [(0, price + (atr * FIBS[x])) for x in RANGE_FIBS]
	return result

def getCandles(ticker, days, interval):
	#today = str(datetime.date.today() - datetime.timedelta(days=1)).split(":")[0]
	startDay = str(datetime.date.today() - datetime.timedelta(days=int(days) + 0)).split(":")[0]
	endDay = str(datetime.date.today() + datetime.timedelta(days=int(days) + 1)).split(":")[0]
	#print( "getCandles - ", startDay, endDay )
	#intervals     tick N/A?, 1min 10 days, 5min 18 days, 15min 18 days
	param = {'symbol': f'{ticker}', 'interval': f'{interval}min', 'start': f'{startDay}', 'end': f'{endDay}', 'session_filter': 'all'}
	return requests.get('https://api.tradier.com/v1/markets/timesales', params=param, headers=TRADIER_HEADER ).json()['series']['data']
def getRecentCandles(ticker, interval):
	param = {'symbol': f'{ticker}', 'interval': f'{interval}min'}
	response = requests.get('https://api.tradier.com/v1/markets/timesales', params=param, headers=TRADIER_HEADER )
	return response.json()['series']['data']
	
#{'date': '2023-10-30', 'open': 4139.39, 'high': 4177.47, 'low': 4132.94, 'close': 4166.82, 'volume': 0}
def getHistory(ticker, days):
	#today = str(datetime.date.today() - datetime.timedelta(days=1)).split(":")[0]
	startDay = str(datetime.date.today() - datetime.timedelta(days=int(days))).split(":")[0]
	endDay = str(datetime.date.today()).split(":")[0]
	#print( "getHistory - ", startDay, endDay )
	#intervals      daily, weekly, monthly
	param = {'symbol': f'{ticker}', 'interval': 'daily', 'start': f'{startDay}', 'end': f'{endDay}', 'session_filter': 'all'}
	return requests.get('https://api.tradier.com/v1/markets/history', params=param, headers=TRADIER_HEADER ).json()['history']['day']
def getHistoryRange(ticker, start, end):
	param = {'symbol': f'{ticker}', 'interval': 'daily', 'start': f'{start}', 'end': f'{end}', 'session_filter': 'all'}
	return requests.get('https://api.tradier.com/v1/markets/history', params=param, headers=TRADIER_HEADER ).json()['history']['day']

def getTodayStatus():
	#{'date': '2023-11-26', 'description': 'Market is closed', 'state': 'closed', 'timestamp': 1700995046, 'next_change': '07:00', 'next_state': 'premarket'}
	return requests.get('https://api.tradier.com/v1/markets/clock', params={}, headers=TRADIER_HEADER).json()['clock']

def getCalendar():
	return requests.get('https://api.tradier.com/v1/markets/calendar', params={}, headers=TRADIER_HEADER).json()['calendar']

def findSPY2SPXRatio():  #Used to Convert SPY to SPX, bypass delayed data
	global SPY2SPXRatio
	spyCandles = getCandles('SPY', 4, 15)
	spxCandles = getCandles('SPX', 4, 15)

	for spx in reversed(spxCandles): 
		for spy in reversed(spyCandles): 
			if spy['time'] == spx['time']:
				SPY2SPXRatio = spx['close'] / spy['close']
				return
#findSPY2SPXRatio() #No longer used.

def cleanHeatmaps():
	files = [f'./heatmap/{f}' for f in os.listdir('./heatmap/')]
	result = []
	files.sort()   #Datestamps should always sort
	while len(files) > 5: 
		tmp = files.pop(0)
		print("removing ", tmp)
		os.remove(tmp)
	return files
	
def loadPastDTE(daysAhead):
	if daysAhead < -5: daysAhead = -5
	if daysAhead > -1: daysAhead = -1
	files = cleanHeatmaps()
	for f in files:
		logDate = json.load(open(f))
		day = next(iter(reversed(logDate)))
		result.append( (day, logDate[day]) )
		#for day in logDate:
		#print( f, ' log reading ', day )
	return result
#loadPastDTE(-5)

#param = {'symbol': 'SPXW231106C04350000', 'interval': '1min', 'start': '2023-11-04', 'end': '2023-11-06', 'session_filter': 'all'}
#response = requests.get('https://api.tradier.com/v1/markets/history',    params=param,    headers=TRADIER_HEADER )
#print( response.json() )

#Running on data-logger.py machine --> python3 -m http.server 8080
#Using a Windows Shortcut  C:\Windows\System32\cmd.com /c "PATH\python3 -m http.server 8080"
#Switched to using HFS File Server
def pullLogFileList():
	""" # For HFS File Server
	response = str(requests.get('http://192.168.1.254:8080/logs/').content)
	response = response.split('<a href="')
	result = []
	for r in response:
		if 'datalog.json"><img src="/' in r: 
			tmp = r.split('datalog.json')[0] + "datalog.json"
			result.append(tmp)
	return result#[tmp.split('">')[0] for tmp in response]
	"""
	# For python3 -m http.server
	response = str(requests.get('http://192.168.1.254:8080').content).split('-datalog.json">')
	del response[0]
	result = [f.split('</a>')[0] for f in response if 'last-datalog.json' not in f]
	#print( result )
	return result
	
lastFileName = ""
lastFileContents = {}  #Store a cached copy of 0dte data for gex-gui.py so we only have to pull the most recent dict entry on the timer
def pullLogFile(fileName, cachedData=False):
	global lastFileName, lastFileContents
	url = f'http://192.168.1.254:8080/{fileName}'
	urlLast = f'http://192.168.1.254:8080/last-datalog.json'
	#url = f'http://192.168.1.254:8080/logs/{fileName}'
	try:
		if lastFileName == fileName or fileName == "SPX":
			#print(1)
			if cachedData : return lastFileContents #blocks a timer in GexGUI
			#print(2)
			tmp = requests.get(urlLast)
			#print(3)
			if tmp.status_code == 404 : return lastFileContents
			#print(4)
			tmp = tmp.json()
			#print(5)
			if fileName == "SPX" : return tmp[next(iter(tmp))]
			#print(6)
			lastFileContents.update( tmp )
			#print(7)
			return lastFileContents
		else :
			lastFileName = fileName
			#print(10)
			#print( url )
			tmp = requests.get(url).content
			#print( tmp.content )
			#print(tmp[:10], " - ", tmp[-10:])  # 93 93 44
			#blnAppend = False
			if tmp[-1] == 44 : 
				tmp = tmp.decode("utf-8")[:-1] + "}"
				#print( tmp[:10] , tmp[-10:] )
				#with open("./logs/test.json", 'a+') as f:
				#	f.seek(0,2)
				#	f.write( tmp )
				#blnAppend = True
			tmp = json.loads(tmp)
			#print(12)
			lastFileContents = tmp
			#if blnAppend :
			#	tmp = requests.get(urlLast).json()
			#	lastFileContents.update( tmp )
			#print(13)
	except Exception as error:
		print(f'pullLogFile Error : {error}')
	return lastFileContents

#************************************* Placing orders ************************************************
def getAccountBalance():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/balances', params={}, headers=TRADIER_HEADER).json()['balances']

def getPositions():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/positions', params={}, headers=TRADIER_HEADER).json()['positions']

def getOrders():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders', params={'page': '3', 'includeTags': 'true'}, headers=TRADIER_HEADER).json()['orders']

def getAnOrder(orderID):
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders/{orderID}', params={'includeTags': 'true'}, headers=TRADIER_HEADER).json()

def cancelOrder(orderID):
	return requests.delete(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders/{orderID}', data={}, headers=TRADIER_HEADER).json()

def modifyOrder(orderID, type, duration, price, stop):
	param = {'type': type, 'duration': duration, 'price': price, 'stop': stop}
	return requests.put(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders/{orderID}', data=param, headers=TRADIER_HEADER)

def placeOptionOrder(symbol, price, ticker = 'XSP', side='buy_to_open', quantity='1', type='limit', duration='day', tag='test', preview='false'):
	param = {'class': 'option', 'symbol': ticker, 'option_symbol': symbol, 'side': side, 'quantity': quantity, 'type': type, 'duration': duration, 'price': price, 'tag': tag, 'preview': preview}
	response = requests.post(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders', data=param, headers=TRADIER_HEADER)
	print(response.status_code)
	return response.json()

#def closeOptionOrder(symbol, price, ticker, side="sell_to_close"
