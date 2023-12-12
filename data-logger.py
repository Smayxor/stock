import datetime
import ujson as json #usjon is json written in C
import requests
#import threading
import time
import schedule
import datapuller as dp
from threading import Timer

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = True
INTERVAL = 60 #Time in seconds between recordings
timer =  None

SPXopenPrice = 0.0#Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned
SPXdayData = {}
SPYopenPrice = 0.0#Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned
SPYdayData = {}
#tenMinutes = 0

class RepeatTimer(Timer):
	def __init__(self, interval, callback, args=None, kwds=None, daemon=True):
		Timer.__init__(self, interval, callback, args, kwds)
		self.daemon = daemon  #Solves runtime error using tkinter from another thread
		
	def run(self):#, daemon=True):
		#self.interval = 60
		while not self.finished.wait(self.interval):
			self.function(*self.args, **self.kwargs)

def save0dte():
	global SPXdayData, SPYdayData
	today = str(datetime.date.today()).split(":")[0]
	fileName = f'./logs/{today}-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(SPXdayData, f)

	fileName = f'./logs/SPY-{today}-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(SPYdayData, f)

def appendData():
	global SPXopenPrice, SPXdayData, SPYopenPrice, SPYdayData, INTERVAL, tenMinutes
	#threading.Timer(INTERVAL, minuteTimerThread).start()
	try:
		price = dp.getQuote('SPY')
		options = dp.getOptionsChain("SPY", 0)
		gex = dp.getGEX( options[1] )
		gex = dp.shrinkToCount(gex, SPYopenPrice, 50)  #Must be centered around same price all day long!!!
		SPYdayData[f'{getStrTime()}'] = {**{'price': price, 'data': gex}}

		price = price * dp.SPY2SPXRatio #dp.getQuote('SPX')
		options = dp.getOptionsChain("SPX", 0)
		gex = dp.getGEX( options[1] )
		gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
		SPXdayData[f'{getStrTime()}'] = {**{'price': price, 'data': gex}}

		#schedule.every(1).minutes.do(minuteTimerThread)
	#	tenMinutes = (tenMinutes + 1) % 10
		save0dte()
	except:
		print('An error occoured')

def startDay():
	global SPXopenPrice, SPXdayData, blnRun, SPYopenPrice, SPYdayData
	state = dp.getMarketHoursToday()['state']
	if 'open' not in state : 
		print( 'Market Closed Today')
		return
	blnRun = True
	SPXdayData = {}
	SPXopenPrice = dp.getQuote('SPX')
	SPYdayData = {}
	SPYopenPrice = dp.getQuote('SPY')
	print( "Day started" )
	timer = RepeatTimer(60, timerThread, daemon=True)
	timer.start()
	#appendData()
	
def endDay():
	global blnRun, SPXdayData, SPYdayData
	if not blnRun : return
	blnRun = False
	today = str(datetime.date.today()).split(":")[0]
	save0dte()
	def savePriceChart(ticker):
		dayCandles = dp.getCandles(ticker, 0, 1)
		fileName = f'./pricelogs/{ticker}-{today}-pricelog.json'
		with open(fileName,'w') as f: 
			json.dump(dayCandles, f)
	print('Finished saving options data')
	savePriceChart('SPX')
	savePriceChart('SPY')
	savePriceChart('VIX')
	savePriceChart('TLT')
	print('Ticker price charts saved.  EOD')

def getStrTime(): return str(datetime.datetime.now()).split(' ')[1].split('.')[0]

def timerThread():
	global blnRun
	if not blnRun : return
	appendData()

print("Running Version 2.0 ArrayOfTuples - NoPandas")
schedule.every().day.at("06:30").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)

#startDay()
#schedule.every().day.at("09:30").do(endDay)

# Loop so that the scheduling task keeps on running all time.
while True: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )