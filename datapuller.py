import datetime
import ujson as json #usjon is json written in C
import requests
import os

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_ACCOUNT_ID = init['TRADIER_ACCOUNT_ID']
del init
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
FIBS = [-1, -0.786, -0.618, -0.5, -0.382, -0.236, 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
RANGE_FIBS = range(len(FIBS))
SPY2SPXRatio = 0

#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk, 12-CallVolume, 13-CallBidSize, 14-CallAskSize, 15-PutVolume, 16-PutBidSize, 17-PutAskSize
GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17

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
def getGEX(options, chartType = 0):  #New test code
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
		volume = option['volume']
		oi = option['open_interest'] 
		
		if chartType == 1: oi = abs(oi - volume) #For Volume charts
		gex = oi * gamma * call
		#exDate = option['expiration_date']
		bid = option['bid']
		ask = option['ask']
		bidSize = option['bidsize']
		askSize = option['asksize']
		#if strike == 4350 : print( option )
		if (len(strikes) == 0) or (strikes[index][0] != strike): #fast, assumes strikes are in order
			strikes.append( [strike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ) 
			index = findIndex(strike) # always make sure we're on the right strike index
		#GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE
		tmp = strikes[index]
		if call == 1: 
			tmp[GEX_STRIKE], tmp[GEX_IV], tmp[GEX_CALL_BID], tmp[GEX_CALL_ASK], tmp[GEX_CALL_VOLUME], tmp[GEX_CALL_BID_SIZE], tmp[GEX_CALL_ASK_SIZE] = strike, iv, bid, ask, volume, bidSize, askSize
			tmp[GEX_CALL_GEX] += gex  #We can have multiple root symbols SPX and SPXW
			tmp[GEX_CALL_OI]+= oi
		else: 
			tmp[GEX_STRIKE], tmp[GEX_IV], tmp[GEX_PUT_BID], tmp[GEX_PUT_ASK], tmp[GEX_PUT_VOLUME], tmp[GEX_PUT_BID_SIZE], tmp[GEX_PUT_ASK_SIZE] = strike, iv, bid, ask, volume, bidSize, askSize
			tmp[GEX_PUT_GEX] += gex
			tmp[GEX_PUT_OI]+= oi
		#strikes[index] = tmp

	for index in range( len(strikes) ):
		strikes[index][GEX_TOTAL_GEX] = strikes[index][GEX_CALL_GEX] + strikes[index][GEX_PUT_GEX]
		strikes[index][GEX_TOTAL_OI] = strikes[index][GEX_CALL_OI] + strikes[index][GEX_PUT_OI]
		#for i in range( 17 ): 		#	if tmp[i] == None: tmp[i] = 0
		strikes[index] = [0 if i is None else i for i in strikes[index]]#filter out any suprises
#		for i in strikes[index]:
#			if i == None: print(f'Failed at {strikes[index]}')		
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
	for x in strikes:  #Locate the most ATM Strike
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
def pullLogFileList():
	response = str(requests.get('http://192.168.1.254:8080').content).split('<a href="', 1)[1].split('<a href="')
	return [tmp.split('">')[0] for tmp in response]
	
def pullLogFile(fileName):
	return requests.get(f'http://192.168.1.254:8080/{fileName}').json()

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

def placeOptionOrder(symbol, price, stop, ticker = 'SPY', side='buy_to_open', quantity='1', type='limit', duration='day', tag='test'):
	param = {'class': 'option', 'symbol': ticker, 'option_symbol': symbol, 'side': side, 'quantity': quantity, 'type': type, 'duration': duration, 'price': price, 'stop': stop, 'tag': tag}
	return requests.post(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders', data=param, headers=TRADIER_HEADER).json()



"""testList = [[4655.0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, 0, 0, 0, 0, 0, 0],
			[4655.0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, 0, 0, 0, 0, 0, 0],
			[4655.0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, 0, 0, 0, 0, 0, 0],
			[5100.0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, 0, 0, 0, 0, 0, 0],
			[5100.0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, 0, 0, 0, 0, 0, 0]]

for i in range(len(testList)): #for entry in testList: #modifying entry wont update testList
	entry = testList[i]	#Makes a copy of values
	testList[i]	= [(0 if j is None else j) for j in testList[i]]#filter out any suprises
	print( entry )
#for entry in testList:
#	entry = [(0 if j is None else j) for j in entry]
#	print( entry )
for x in testList: print(x)"""
