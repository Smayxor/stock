import datetime
import ujson as json #usjon is json written in C
import requests
import time
import schedule
import datapuller as dp

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = False
timer =  None

SPX0DTEdayData = {}
SPX1DTEdayData = {}
SPXopenPrice = -1 #Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned
skip1DTE = 0

def save0dte():
	global SPX0DTEdayData, SPX1DTEdayData
	today = str(datetime.date.today()).split(":")[0]
	fileName = f'./logs/{today}-0dte-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(SPX0DTEdayData, f)

	fileName = f'./logs/{today}-1dte-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(SPX1DTEdayData, f)

def appendData():
	global SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE
	try:
		options = dp.getOptionsChain("SPX", 0)
		gex = dp.getGEX( options[1] )
		price = gex[0][dp.GEX_STRIKE] + ((gex[0][dp.GEX_CALL_BID] + gex[0][dp.GEX_CALL_ASK]) / 2)
		if SPXopenPrice == -1: SPXopenPrice = price
		gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
		#SPX0DTEdayData[getStrTime()] = {**{'price': price, 'data': gex}}
		SPX0DTEdayData[getStrTime()] = gex
		if skip1DTE == 0:
			options = dp.getOptionsChain("SPX", 1)
			gex = dp.getGEX( options[1] )
			gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
			SPX1DTEdayData[getStrTime()] = gex
			#SPX1DTEdayData[getStrTime()] = {**{'price': price, 'data': gex}}
		skip1DTE = (skip1DTE + 1) % 15		
		
		save0dte()
	except:
		print('An error occoured')

def startDay():
	global blnRun, SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE
	state = dp.getMarketHoursToday()
	print( state )
	if 'closed' in state['state'] : #Seems to not apply to sunday!!!
		#{'date': '2023-12-17', 'description': 'Market is closed', 'state': 'closed', 'timestamp': 1702808042, 'next_change': '07:00', 'next_state': 'premarket'}
		print( 'Market Closed Today')
		return
	if datetime.datetime.now().weekday() > 4 : return
	
	blnRun = True
	SPX0DTEdayData = {}
	SPXopenPrice = -1
	SPX1DTEdayData = {}
	skip1DTE = 0
	print( "Day started" )
	
def endDay():
	global blnRun, SPX0DTEdayData, SPX1DTEdayData
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
	#savePriceChart('SPX')
	#savePriceChart('SPY')
	#savePriceChart('VIX')
	#savePriceChart('TLT')
	#print('Ticker price charts saved.  EOD')

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01) #return str(datetime.datetime.now()).split(' ')[1].split('.')[0]

def timerThread():
	global blnRun
	if not blnRun : return
	appendData()

print("Running Version 2.0 ArrayOfTuples - NoPandas")
schedule.every().day.at("04:30").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)

timer = dp.RepeatTimer(20, timerThread, daemon=True)
timer.start()
#now = datetime.datetime.now()
tmp = getStrTime()#(now.hour * 100) + now.minute
if (tmp > 430) and (tmp < 1300): 
	print('Late start to the day')
	startDay()
#startDay()

# Loop so that the scheduling task keeps on running all time.
while True: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )