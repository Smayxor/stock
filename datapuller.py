import datetime
import ujson as json #usjon is json written in C
from threading import Timer
import requests
#from requests import Request, Session
import os
import heapq
import asyncio

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_ACCOUNT_ID = init['TRADIER_ACCOUNT_ID']
SERVER_IP = init.get('SERVER_IP', 'http://127.0.0.1:8080')  #need to switch all init[] commands to use .get()  so default values can be assigned
FRED_KEY = init.get('FRED', None)
IS_SERVER = SERVER_IP == 'http://127.0.0.1:8080'
del init
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
FIBS = [-1, -0.786, -0.618, -0.5, -0.382, -0.236, 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
RANGE_FIBS = range(len(FIBS))
SPY2SPXRatio = 0 # No longer used
INDICES = ['SPX', 'VIX', 'XSP', 'SOX']
SPX0DTEDate, SPX0DTEDate = None, None

GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_CALL_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL, GEX_PUT_IV, GEX_CALL_DELTA, GEX_PUT_DELTA = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22

if not os.path.isdir('./logs'): os.mkdir('./logs')

#when XLE is down but CL is up, that means everybody is selling off and flying to safety assets ( oil & gold - gold is barely red while the rest of the market is -1% or weaker ) 
#idk why michigan gets such a focus of attention, they survey / cold-call 'random' people and that's where they get their sentiment polls from
#just like the st louis FED get's the spotlight above the others

"""
from requests import Request, Session

s = Session()
req = Request('GET',  url, data=data, headers=headers)

prepped = s.prepare_request(req)

# do something with prepped.body
prepped.body = 'Seriously, send exactly these bytes.'

# do something with prepped.headers
prepped.headers['Keep-Dead'] = 'parrot'

resp = s.send(prepped,
    stream=stream,
    verify=verify,
    proxies=proxies,
    cert=cert,
    timeout=timeout
)

print(resp.status_code)


# Merge environment settings into session
settings = s.merge_environment_settings(prepped.url, {}, None, None, None)
resp = s.send(prepped, **settings)

print(resp.status_code)




from requests.auth import HTTPBasicAuth
auth = HTTPBasicAuth('fake@example.com', 'not_a_real_password')

r = requests.post(url=url, data=body, auth=auth)
r.status_code



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
def addDebugLog(self, data):
	try:
		def saveDataFile(bigData, appendData, myFile):
			if not os.path.isfile(myFile):
				with open(myFile,'w') as f: 
					json.dump(bigData, f)
			else:
				if appendData == "" : 
					print( 'Empty String')
					return
				if len( appendData ) == 0 :
					print(f'No data on write')
					return
				with open(myFile, 'rb+') as f:
					f.seek(-1,os.SEEK_END)
					outData = json.dumps(appendData).replace('{', ',')
					f.write( outData.encode() )		
		saveDataFile( self.Data, gex, self.FileName )
	except Exception as error:
		print( f'DebugLog - {error}' )
	return None
		
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

def findKeyLevels(strikes):
	price = getPrice(ticker="SPX", strikes=strikes)
	hasValueList = [x for x in strikes if (x[GEX_STRIKE] > price and x[GEX_CALL_BID] > 0.3) or (x[GEX_STRIKE] < price and x[GEX_PUT_BID] > 0.3)]
	main3 = heapq.nlargest( 5, hasValueList, key=lambda i: i[GEX_TOTAL_OI])
	return [x[GEX_STRIKE] for x in main3]
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
	"""

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
	response = requests.get('https://api.tradier.com/v1/markets/clock', params={'delayed': 'false'}, headers=TRADIER_HEADER)
	if response.status_code != 200 : print( 'getMarketHoursToday ', response.status_code, response.content )
	return response.json()['clock']

def getExpirations(ticker):
	param = {'symbol': f'{ticker}', 'includeAllRoots': 'true', 'strikes': 'false'}   #'strikes': 'true'}
	response = requests.get('https://api.tradier.com/v1/markets/options/expirations', params=param, headers=TRADIER_HEADER)
	if response.status_code != 200 : print( 'getExpirations ', response.status_code, response.content )
	return response.json()['expirations']['date']

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
		if result in dates: break
		dte += 1
	return result

"""
import multiprocessing
import requests

def call_with_timeout(func, args, kwargs, timeout):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    # define a wrapper of `return_dict` to store the result.
    def function(return_dict):
        return_dict['value'] = func(*args, **kwargs)

    p = multiprocessing.Process(target=function, args=(return_dict,))
    p.start()

    # Force a max. `timeout` or wait for the process to finish
    p.join(timeout)

    # If thread is still active, it didn't finish: raise TimeoutError
    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError
    else:
        return return_dict['value']

call_with_timeout(requests.get, args=(url,), kwargs={'timeout': 10}, timeout=60)
"""

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
	with open(f'./logs/crash.json', 'w') as f:
		json.dump(response, f)
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
	with open(f'./logs/crash.json', 'w') as f:
		json.dump(response, f)
	#*********************************************************************************************************************************************
	options = response.get('options', dict({'a': 123})).get('option', None)
	if options is None :
		print(f'Unexpected response in getOptionsChain - {response}')
		return None
	return (expDate, options)





async def asyncGetOptionsChains(ticker, dte, date=None):
	return getOptionsChain(ticker, dte, date=None)

def getMultipleDTEOptionChain(ticker, days):
	exps = getExpirations(ticker)
	#if today == exps[0] : exps.pop(0)
	exps = exps[:days]
	days = []
	for exp in exps:
		param = {'symbol': f'{ticker}', 'expiration': f'{exp}', 'greeks': 'true'}
		response = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER )
		if response.status_code != 200 : print( 'getMultipleDTEOptionChain ', response.status_code, response.content )
		options = response.json()['options']['option']
		gex = getGEX( options )
		days.append( (exp, gex) )
	return days

#{'symbol': 'SPY231030C00499000', 'description': 'SPY Oct 30 2023 $499.00 Call', 'exch': 'Z', 'type': 'option', 'last': 0.01, 'change': 0.0, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.01, 'underlying': 'SPY', 'strike': 499.0, 'greeks': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 2e-05, 'rho': 0.0, 'phi': 0.0, 'bid_iv': 0.0, 'mid_iv': 0.716638, 'ask_iv': 0.716638, 'smv_vol': 0.16, 'updated_at': '2023-10-27 20:00:01'}, 'change_percentage': 0.0, 'average_volume': 0, 'last_volume': 11, 'trade_date': 1697812231388, 'prevclose': 0.01, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'Q', 'bid_date': 1698437676000, 'asksize': 5608, 'askexch': 'X', 'ask_date': 1698437691000, 'open_interest': 36, 'contract_size': 100, 'expiration_date': '2023-10-30', 'expiration_type': 'weeklys', 'option_type': 'call', 'root_symbol': 'SPY'}
#{'symbol': 'SPXW240216P00200000', 'description': 'SPXW Feb 16 2024 $200.00 Put', 'exch': 'C', 'type': 'option', 'last': None, 'change': None, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.05, 'underlying': 'SPX', 'strike': 200.0, 'greeks': {'delta': -2.25e-14, 'gamma': -3.2575160249757252e-15, 'theta': 2.236129405855236e-11, 'vega': 2.0000060368178682e-05, 'rho': 0.0, 'phi': 0.0, 'bid_iv': 0.0, 'mid_iv': 0.0, 'ask_iv': 0.0, 'smv_vol': 0.42, 'updated_at': '2024-02-15 20:59:59'}, 'change_percentage': None, 'average_volume': 0, 'last_volume': 0, 'trade_date': 0, 'prevclose': None, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'C', 'bid_date': 1708093802000, 'asksize': 1067, 'askexch': 'C', 'ask_date': 1708095327000, 'open_interest': 9, 'contract_size': 100, 'expiration_date': '2024-02-16', 'expiration_type': 'standard', 'option_type': 'put', 'root_symbol': 'SPXW'}
#{'symbol': 'SPX240216P00400000', 'description': 'SPX Feb 16 2024 $400.00 Put', 'exch': 'C', 'type': 'option', 'last': 0.05, 'change': 0.0, 'volume': 0, 'open': None, 'high': None, 'low': None, 'close': None, 'bid': 0.0, 'ask': 0.15, 'underlying': 'SPX', 'strike': 400.0, 'greeks': {'delta': -1.338e-13, 'gamma': -1.9037189917344295e-14, 'theta': -0.19774195063757755, 'vega': 2.0000113384843898e-05, 'rho': 0.0005479309221920519, 'phi': -0.006882528396090493, 'bid_iv': 0.0, 'mid_iv': 0.0, 'ask_iv': 0.0, 'smv_vol': 1.134, 'updated_at': '2024-02-15 20:59:59'}, 'change_percentage': 0.0, 'average_volume': 0, 'last_volume': 1, 'trade_date': 1705501802447, 'prevclose': 0.05, 'week_52_high': 0.0, 'week_52_low': 0.0, 'bidsize': 0, 'bidexch': 'C', 'bid_date': 1708032417000, 'asksize': 0, 'askexch': 'C', 'ask_date': 1708045200000, 'open_interest': 1080, 'contract_size': 100, 'expiration_date': '2024-02-16', 'expiration_type': 'standard', 'option_type': 'put', 'root_symbol': 'SPX'}
def getGEX(options):  #An increase in IV hints at Retail Buying = High IV is Handicapping
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
			strikes.append( [strike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "None", "None", 0, 0, 0])#, 0, 0] ) 
			index = findIndex(strike) # always make sure we're on the right strike index
		#GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_CALL_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL, GEX_PUT_IV, GEX_CALL_DELTA, GEX_PUT_DELTA
		tmp = strikes[index]
		if call == 1: 
			tmp[GEX_STRIKE], tmp[GEX_CALL_IV], tmp[GEX_CALL_BID], tmp[GEX_CALL_ASK], tmp[GEX_CALL_VOLUME], tmp[GEX_CALL_BID_SIZE], tmp[GEX_CALL_ASK_SIZE], tmp[GEX_CALL_DELTA] = strike, iv, bid, ask, volume, bidSize, askSize, delta
			tmp[GEX_CALL_GEX] += gex  #We can have multiple root symbols SPX and SPXW
			tmp[GEX_CALL_OI]+= oi
			tmp[GEX_CALL_SYMBOL] = symbol
			#tmp[GEX_CALL_THETA] = thetaXrho
		else: 
			tmp[GEX_STRIKE], tmp[GEX_PUT_IV], tmp[GEX_PUT_BID], tmp[GEX_PUT_ASK], tmp[GEX_PUT_VOLUME], tmp[GEX_PUT_BID_SIZE], tmp[GEX_PUT_ASK_SIZE], tmp[GEX_PUT_DELTA] = strike, iv, bid, ask, volume, bidSize, askSize, delta
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

lastPrice = 0
def getPrice(ticker, strikes = None, dte = "now"):#, test=False):
	global lastPrice
	
	if 1==1: #ticker in INDICES and strikes != None:
		#*************************************************************************************************************
		# Needs to correctly factor in value from DTE
		#**************************************************************************************************************
		#if 'now' in dte: dte = str(datetime.datetime.now()).split(' ')[0]
		#end_date = datetime.datetime.strptime(dte, '%Y-%m-%d')
		#num_days = (end_date - datetime.datetime.now()).days + 1
		#num_weekends = num_days // 7
		#dte = num_days - (num_weekends * 2)
		
		firstStrike = strikes[0]
		lastStrike = strikes[-1]
		
		if dte != 'now' :
			#end_date = datetime.datetime.strptime(dte, '%Y-%m-%d')
			#num_days = (end_date - datetime.datetime.now()).days + 1
			#num_weekends = num_days // 7
			#trading_days = num_days - (num_weekends * 2)
			#print( end_date, num_days, num_weekends, trading_days )

			#callPrice = firstStrike[GEX_STRIKE] + ((firstStrike[GEX_CALL_BID] + firstStrike[GEX_CALL_ASK]) / 2)
			#putPrice = lastStrike[GEX_STRIKE] -((lastStrike[GEX_PUT_BID] + lastStrike[GEX_PUT_ASK]) / 2)

			blnCalls = firstStrike[GEX_CALL_DELTA] < (lastStrike[GEX_PUT_DELTA] * -1)

	#print( firstStrike[GEX_CALL_DELTA], firstStrike[GEX_PUT_DELTA], firstStrike[GEX_CALL_DELTA], firstStrike[GEX_CALL_DELTA] )

	cp = firstStrike[GEX_STRIKE] + firstStrike[GEX_CALL_BID]
	pp = lastStrike[GEX_STRIKE] - lastStrike[GEX_PUT_BID]

	price = cp if cp<pp and firstStrike[GEX_CALL_BID] != 0 else pp
	
	return price
		
	#else: price = getQuote(ticker)  #Trying to not use the extra API Request if not needed
	#return price
"""
S = underlying price ($$$ per share)
K = strike price ($$$ per share)
σ = volatility (% p.a.)
r = continuously compounded risk-free interest rate (% p.a.)
q = continuously compounded dividend yield (% p.a.)
t = time to expiration (% of year)
"""
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
	# For python3 -m http.server
	if IS_SERVER : return [x for x in os.listdir('./logs') if '-datalog.json' in x and 'last-datalog.json' not in x]
	response = str(requests.get(SERVER_IP).content).split('-datalog.json">')
	del response[0]
	result = [f.split('</a>')[0] for f in response if 'last-datalog.json' not in f]
	return result

def pullLogFileListGME():
	# For python3 -m http.server
	if IS_SERVER : return [x for x in os.listdir('./logs') if 'GME.json' in x]
	response = str(requests.get(SERVER_IP).content).split('GME.json">')
	del response[0]
	result = [f.split('</a>')[0] for f in response]
	return result

def getToday():
	global testTime
	dn = datetime.datetime.now()
	dateAndtime = str(dn).split(" ")	#2024-04-05 21:57:32.688823
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 100) + float(tmp[1]) + (float(tmp[2]) * 0.01)
	if minute > 1500 :
		dn = str(dn + datetime.timedelta(1)).split(" ")[0]
	else:
		dn = dateAndtime[0]
	return (dn, minute)
	
lastFileName = ""
lastFileContents = {}  #Store a cached copy of 0dte data for gex-gui.py so we only have to pull the most recent dict entry on the timer

dateAndTime = getToday()[0] # str(datetime.datetime.now()).split(" ")[0]
print(f'Target Date - {dateAndTime}')
cacheFiles = os.listdir('./logs')
lastFileKeyList = []
blnWasFinal = False

#SERVER_IP = None
def grabLastData():
	urlLast = f'{SERVER_IP}/last-datalog.json'
	tmp = requests.get(urlLast).json()
	
def pullLogFile(fileName, cachedData=False, discordBot=False) :
	global lastFileName, lastFileContents, lastFileKeyList, blnWasFinal
	url = f'{SERVER_IP}/{fileName}'
	urlLast = f'{SERVER_IP}/last-datalog.json'
	
	blnSaveACopy = False #Store a copy of data locally
	if not dateAndTime in fileName : # Only grab cached files for previous days
		if fileName in cacheFiles : 
			if lastFileName == fileName : 
				pass
			else:
				#lastFileContents = {}
				lastFileContents = json.load(open(f'./logs/{fileName}'))
				lastFileName = fileName
			return lastFileContents
		else :
			blnSaveACopy = True
	#If data is not stored locally, lets grab it
	try:
		if discordBot :
			lastFileName = ""
			lastFileContents = {}
		
		
		if (lastFileName == fileName or fileName == "SPX") :# and not discordBot
			if cachedData : return lastFileContents #blocks a timer in GexGUI
			tmp = None
			
			if IS_SERVER :
				tmp = json.load(open(f'./logs/last-datalog.json'))
			else:
				tmp = requests.get(urlLast)
				if tmp.status_code == 404 : return lastFileContents
				tmp = tmp.json()
			blnFinal = tmp['final']
			tmp.pop('final', None )
			#print( [getPrice("SPX", v) for k, v in tmp.items() ] )
			if blnWasFinal and blnFinal == True : return lastFileContents
				
			for keys in lastFileKeyList :
				lastFileContents.pop( keys, None )
				if keys in list(lastFileContents.keys()) : print( 'Fail')
				
			tmpKeys = list(tmp.keys())
			lastFileKeyList = [tmpKeys[-1], tmpKeys[-2]] if blnFinal else tmpKeys #We still need to pop the CurrentClose

			blnWasFinal = blnFinal
			#if fileName == "SPX" : return tmp[next(iter(tmp))]   #WTF Is this even for??!?!?!??!
			lastFileContents.update( tmp )
			
			return lastFileContents
		else :
			lastFileName = fileName
			if IS_SERVER :
				tmp = json.load(open(f'./logs/{fileName}'))
			else :
				tmp = requests.get(url).content
				if tmp[-1] == 44 : 
					tmp = tmp.decode("utf-8")[:-1] + "}"
				tmp = json.loads(tmp)
		
			lastFileContents = tmp
			if blnSaveACopy and not discordBot and IS_SERVER == False :#Storing a cached copy of all data from previous days (today might be in progress)
				with open(f'./logs/{fileName}', 'w') as f:
					json.dump(lastFileContents, f)
			#if discordBot : return lastFileContents
	except Exception as error :
		print(f'pullLogFile Error : {error}')
	return lastFileContents

#************************************* Placing orders ************************************************
def getAccountBalance():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/balances', params={}, headers=TRADIER_HEADER).json()['balances']

def getPositions():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/positions', params={}, headers=TRADIER_HEADER).json()['positions']

def getOrders():
	return requests.get(f'https://api.tradier.com/v1/accounts/{TRADIER_ACCOUNT_ID}/orders', params={ 'includeTags': 'true'}, headers=TRADIER_HEADER).json()['orders']

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


#   https://fred.stlouisfed.org/    use symbol DGS3MO    DGS6MO    DGS1    DGS2   DGS3   DGS5    DGS7    DGS10
# import  pandas_datareader.data  as web         __get_rate__

"""
if not FRED_KEY is None :
	print('We got FRED')
	fredURL = f'https://api.stlouisfed.org/fred/releases?api_key={FRED_KEY}&file_type=json&realtime_start=2023-01-01&realtime_end=9999-12-31'
	fredURL = f'https://api.stlouisfed.org/fred/category/series?category_id=9&api_key={FRED_KEY}&file_type=json&realtime_start=2023-01-01&realtime_end=9999-12-31'
	#fredURL = f'https://fred.stlouisfed.org/releases/calendar?rid=10&y=2021'
	response = requests.get(fredURL)
	
	print( response.content)
	if response.status_code == 200 :
		response = response.json()
		for release in response["seriess"] :
			print( release )
			#print( release["id"], release["realtime_start"], release["name"], release["press_release"] )
"""	

#{'id': 'COREFLEXCPIM157SFRBATL', 'realtime_start': '2023-01-01', 'realtime_end': '9999-12-31', 'title': 'Flexible Price Consumer Price Index less Food and Energy', 'observation_start': '1967-01-01', 'observation_end': '2024-06-01', 'frequency': 'Monthly', 'frequency_short': 'M', 'units': 'Percent Change', 'units_short': '% Chg.', 'seasonal_adjustment': 'Seasonally Adjusted', 'seasonal_adjustment_short': 'SA', 'last_updated': '2024-07-11 12:01:12-05', 'popularity': 4, 'group_popularity': 35, 'notes': 'The Flexible Price Consumer Price Index (CPI) is calculated from a subset of goods and services included in the CPI that change price relatively frequently. Because flexible prices are quick to change, it assumes that when these prices are set, they incorporate less of an expectation about future inflation. Evidence suggests that this flexible price measure is more responsive to changes in the current economic environment or the level of economic slack.\n\nTo obtain more information about this release see: Michael F. Bryan, and Brent H. Meyer. “Are Some Prices in the CPI More Forward Looking Than Others? We Think So.” Economic Commentary (Federal Reserve Bank of Cleveland) (May 19, 2010): 1–6. https://doi.org/10.26509/frbc-ec-201002 (https://doi.org/10.26509/frbc-ec-201002).'}