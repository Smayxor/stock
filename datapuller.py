import datetime
import ujson as json #usjon is json written in C
import requests
import os

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
del init
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
FIBS = [-1, -0.786, -0.618, -0.5, -0.382, -0.236, 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
RANGE_FIBS = range(len(FIBS))
SPY2SPXRatio = 0

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
	expDate = getExpirationDate(ticker, dte)
	param = {'symbol': f'{ticker}', 'expiration': f'{expDate}', 'greeks': 'true'}
	options = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER ).json()['options']['option']
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
def getGEX(options):
	index = 0
	strikes = []
	def findIndex( strike ): #loop from end of list, confirm we are using correct index
		index = len(strikes) - 1
		while strikes[index][0] != strike: index -= 1
		return index
	
	for option in options:
		strike = option['strike'] 
		call = 1 if option['option_type'] == 'call' else -1
		gamma = 0 
		iv = 0
		if option['greeks'] is not None:
			gamma = option['greeks']['gamma']
			iv = option['greeks']['mid_iv']
		oi = option['open_interest']
		volume = option['volume']
		gex = oi * gamma * call
		#exDate = option['expiration_date']
		bid = option['bid']
		ask = option['ask']
		bidSize = option['bidsize']
		askSize = option['asksize']
		#if strike == 4350 : print( option )
		if (len(strikes) == 0) or (strikes[index][0] != strike): #fast, assumes strikes are in order
			strikes.append( (strike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) ) #0-Strike, 1-CallGEX, 2-CallOI,  3-PutGEX, 4-PutOI, 5-IV, 6-CallBid, 7-CallAsk, 8-PutBid, 9-PutAsk, 10-CallVolume, 11-CallBidSize, 12-CallAskSize, 13-PutVolume, 14-PutBidSize, 15-PutAskSize
			index = findIndex(strike) # always make sure we're on the right strike index
		#combine tuples for that specific strike.  Combine Calls + Puts + DifferentRootSymbol - SPX/SPXW
		if call == 1: strikes[index] = (strike, strikes[index][1] + gex, strikes[index][2] + oi, strikes[index][3], strikes[index][4], iv, bid, ask, strikes[index][8], strikes[index][9], volume, bidSize, askSize, strikes[index][13], strikes[index][14], strikes[index][15])
		else: strikes[index] = (strike, strikes[index][1], strikes[index][2], strikes[index][3] + gex, strikes[index][4] + oi, iv, strikes[index][6], strikes[index][7], bid, ask, strikes[index][10], strikes[index][11], strikes[index][12], volume, bidSize, askSize)
	for index in range( len(strikes) ):
		strike = strikes[index]
		totalOI = strike[2] + strike[4]
		totalGEX = strike[1] + strike[3]
		strike = (strike[0], totalGEX, totalOI, strike[1], strike[2], strike[3], strike[4], strike[5], strike[6], strike[7], strike[8], strike[9], strike[10], strike[11], strike[12], strike[13], strike[14], strike[15] )#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk, 12-CallVolume, 13-CallBidSize, 14-CallAskSize, 15-PutVolume, 16-PutBidSize, 17-PutAskSize
		for i in range( 17 ):  #filter out any suprises
			if strike[i] == None:
				tmp = list( strike )
				tmp[i] = 0
				strike = tuple(tmp)

		strikes[index] = strike
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
	atmStrike = 0.0
	dist = 99999
	for x in strikes:
		thisDist = abs(x[0] - price)
		if thisDist < dist:
			atmStrike = x[0]
			dist = thisDist
	i = len(strikes) -1
	while (len(strikes) > count) and i > -1:
		matches = 0
		dist = abs(atmStrike - strikes[i][0])
		for j in strikes: 
			if abs(atmStrike - j[0]) < dist : matches += 1 
		if matches > count: strikes.pop(i) 
		i -= 1
	return strikes

def getQuote(ticker):
	param = {'symbols': 'SPY', 'greeks': 'false'} if ticker == 'SPX' else {'symbols': f'{ticker}', 'greeks': 'false'}
	#param = {'symbols': f'{ticker}', 'greeks': 'false'}
	result = requests.get('https://api.tradier.com/v1/markets/quotes', params=param, headers=TRADIER_HEADER).json()['quotes']['quote']['last']
	if ticker == 'SPX' : result *= SPY2SPXRatio
	return result

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
#{'date': '2023-10-30', 'open': 4139.39, 'high': 4177.47, 'low': 4132.94, 'close': 4166.82, 'volume': 0}
def getHistory(ticker, days):
	#today = str(datetime.date.today() - datetime.timedelta(days=1)).split(":")[0]
	startDay = str(datetime.date.today() - datetime.timedelta(days=int(days))).split(":")[0]
	endDay = str(datetime.date.today()).split(":")[0]
	#print( "getHistory - ", startDay, endDay )
	#intervals      daily, weekly, monthly
	param = {'symbol': f'{ticker}', 'interval': 'daily', 'start': f'{startDay}', 'end': f'{endDay}', 'session_filter': 'all'}
	return requests.get('https://api.tradier.com/v1/markets/history', params=param, headers=TRADIER_HEADER ).json()['history']['day']

def findSPY2SPXRatio():  #Used to Convert SPY to SPX, bypass delayed data
	global SPY2SPXRatio
	spyCandles = getCandles('SPY', 4, 15)
	spxCandles = getCandles('SPX', 4, 15)

	for spy in spyCandles: 
		for spx in spxCandles: 
			if spy['time'] == spx['time']:
				SPY2SPXRatio = spx['high'] / spy['high']
				return
findSPY2SPXRatio()

def loadPastDTE():
	files = [f'./heatmap/{f}' for f in os.listdir('./heatmap/')]
	result = []
	"""
	for prevFiles in files:
		tmpName = prevFiles.split('/')[2].split('-', 1)[1].split('.json')[0]
		date1 = datetime.datetime.strptime(tmpName, "%Y-%m-%d")
		date2 = datetime.datetime.now()
		difference = (date2 - date1).days
		#print(f'Past GEX {difference} days')
	"""
	lastDay = files[-1]
	print( f'Comparing to {lastDay}' )
	jsonData = json.load(open(lastDay))
	
	for day in jsonData:
		gexData = jsonData[day]
		result.append( (day, gexData) )
	#for prevFile in files:
	#	jsonData = json.load(open(prevFile))
		#day = next(iter(jsonData))   #ONLY GRABBING THE FIRST DAY
	#	for day in jsonData:
	#		gexData = jsonData[day]
	#		result.append( (day, gexData) )
	return result
#loadPastDTE()

#param = {'symbol': 'SPXW231106C04350000', 'interval': '1min', 'start': '2023-11-04', 'end': '2023-11-06', 'session_filter': 'all'}
#response = requests.get('https://api.tradier.com/v1/markets/history',    params=param,    headers=TRADIER_HEADER )
#print( response.json() )