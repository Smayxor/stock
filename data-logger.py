import datetime
import ujson as json #usjon is json written in C
import requests
import threading
import time
import schedule
import pandas as pd

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = True

openPrice = 0.0
dayData = {}

#dailyTaskTime = datetime.time(hour=13, minute=31, tzinfo=datetime.timezone.utc)
	
def startDay():
	global openPrice, dayData
	print( "Day started" )
	#schedule.every(1).minutes.do(minuteTimerThread)
	openPrice = getQuote('SPX')['last']
	dayData[f'{getStrTime()}'] = {**{'price': openPrice, **getOptionsChain("SPX", openPrice).to_dict()}}
	threading.Timer(60, minuteTimerThread).start()

def endDay():
	global dayData, blnRun
	blnRun = False
	today = str(datetime.date.today()).split(":")[0]
	fileName = f'./logs/{today}-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(dayData, f)
	print("Saving Data ", len(dayData))

def getStrTime(): return str(datetime.datetime.now()).split(' ')[1].split('.')[0]

def getQuote(ticker):
	param={'symbols': f'{ticker}', 'greeks': 'false'}
	return requests.get('https://api.tradier.com/v1/markets/quotes', params=param, headers=TRADIER_HEADER).json()['quotes']['quote']

def minuteTimerThread():
	global openPrice, dayData, blnRun
	if not blnRun : return
	threading.Timer(60, minuteTimerThread).start()
	
	price = getQuote('SPX')['last']
	timeNow = getStrTime()
	dayData[f'{timeNow }'] = {**{'price': price}, **getOptionsChain("SPX", openPrice).to_dict()}
	print("Recording - ", timeNow)
	
def getOptionsChain(ticker, price):	
	today = datetime.date.today()
	dte = 1
	dateRange = str(today + datetime.timedelta(days=int(dte))).split(":")[0]
	param = {'symbol': f'{ticker}', 'expiration': f'{dateRange}', 'greeks': 'true'}
	options = requests.get('https://api.tradier.com/v1/markets/options/chains', params=param, headers=TRADIER_HEADER ).json()['options']['option']
	options = pd.DataFrame.from_dict(options)
	options = options.drop(columns=['symbol', 'description', 'exch', 'type', 'last', 'change', 'open', 'high', 'low', 'close', 'underlying', 'change_percentage', 'average_volume', 'last_volume', 'trade_date', 'prevclose', 'week_52_high', 'week_52_low', 'bidexch', 'bid_date', 'askexch', 'ask_date', 'contract_size', 'expiration_date', 'expiration_type', 'root_symbol'], axis=1)
	options = options[(options['strike'] > price - 100) & (options['strike'] < price + 100)]
	options = pd.concat([options, options["greeks"].apply(pd.Series)], axis=1)
	options = options.drop(columns=['greeks', 'theta', 'vega', 'rho', 'phi', 'bid_iv', 'ask_iv', 'smv_vol', 'updated_at'])
	options = options.reset_index(drop = True)
	return options

print( datetime.date.today() )
schedule.every().day.at("06:30").do(startDay)
schedule.every().day.at("13:00").do(endDay)

# Loop so that the scheduling task keeps on running all time.
while blnRun: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )