import datetime
import ujson as json #usjon is json written in C
import requests
import time
import schedule
import datapuller as dp
from threading import Timer

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = False
timer =  None

SPXdayData = {}
SPYdayData = {}
SPYopenPrice = -1#Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned.  Reduces file size by 2/3
SPXopenPrice = -1#Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned

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
	global SPXdayData, SPYdayData, SPXopenPrice, SPYopenPrice
	try:
		options = dp.getOptionsChain("SPY", 0)
		gex = dp.getGEX( options[1] )
		price = gex[0][dp.GEX_STRIKE] + ((gex[0][dp.GEX_CALL_BID] + gex[0][dp.GEX_CALL_ASK]) / 2)
		if SPYopenPrice == -1: SPYopenPrice = price
		gex = dp.shrinkToCount(gex, SPYopenPrice, 50)  #Must be centered around same price all day long!!!
		SPYdayData[f'{getStrTime()}'] = {**{'price': price, 'data': gex}}

		options = dp.getOptionsChain("SPX", 0)
		gex = dp.getGEX( options[1] )
		price = gex[0][dp.GEX_STRIKE] + ((gex[0][dp.GEX_CALL_BID] + gex[0][dp.GEX_CALL_ASK]) / 2)
		if SPXopenPrice == -1: SPXopenPrice = price
		gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
		SPXdayData[f'{getStrTime()}'] = {**{'price': price, 'data': gex}}

		save0dte()
	except:
		print('An error occoured')

def startDay():
	global blnRun, SPXdayData, SPYdayData, SPXopenPrice, SPYopenPrice
	state = dp.getMarketHoursToday()
	print( state )
	if 'open' not in state['state'] : #Seems to not apply to sunday!!!
		#{'date': '2023-12-17', 'description': 'Market is closed', 'state': 'closed', 'timestamp': 1702808042, 'next_change': '07:00', 'next_state': 'premarket'}
		print( 'Market Closed Today')
		return
	if datetime.datetime.now().weekday() > 4 : return
	
	blnRun = True
	SPXdayData = {}
	SPXopenPrice = -1# dp.getQuote('SPX')
	SPYdayData = {}
	SPYopenPrice = -1#dp.getQuote('SPY')
	print( "Day started" )
	
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

timer = RepeatTimer(60, timerThread, daemon=True)
timer.start()
now = datetime.datetime.now()
tmp = (now.hour * 100) + now.minute
if (tmp > 630) and (tmp < 1300): 
	print('Late start to the day')
	startDay()
#startDay()

# Loop so that the scheduling task keeps on running all time.
while True: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )