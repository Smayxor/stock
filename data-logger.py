import datetime
import ujson as json #usjon is json written in C
import requests
import time
import schedule
import datapuller as dp
import os

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = False
timer =  None

SPX0DTEdayData = {}
SPX1DTEdayData = {}
SPXLastData = {}
SPXopenPrice = -1 #Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned
skip1DTE = 0
skipPreMarket = 0


"""# start of the script   ***** How to cache local file
# load the current value
import ast
status, status_file = False, "state.txt"
with open(status_file) as stat_file:
    status = ast.literal_eval(next(stat_file()))

# keep on looping, check against *known value*
while True:
    current_status = get_door_status()
    if current_status != status:  # only update on changes
        status = current_status  # update internal variable
        # open for writing overwrites previous value
        with open(status_file, 'w') as stat_file:
            stat_file.write(status)"""

"""
'r' Read only: the default
'w' Write: Create a new file or overwrite the contents of an existing file.
'a' Append: Write data to the end of an existing file.
'r+' Both read and write to an existing file. The file pointer will be at the beginning of the file.
'w+' Both read and write to a new file or overwrite the contents of an existing file.
'a+' Both read and write to an existing file or create a new file. The file pointer will be at the end of the file.
"""

def save0dte(bln1dte):
	global SPX0DTEdayData, SPX1DTEdayData, SPXLastData
	today = str(datetime.date.today()).split(":")[0]
	
	def saveDataFile(bigData, appendData, myFile):
		if not os.path.isfile(myFile):
			#print(f'Creating file {myFile} x {len(bigData)}')
			with open(myFile,'w') as f: 
				json.dump(bigData, f)
		else:
			#fileSize = os.stat(myFile).st_size
			#print(f'Appending file {myFile} x {fileSize}')
			#appendData = "," + json.dumps(appendData)[1:]
			if appendData == "" : 
				print( 'Empty String')
				return
				
			with open(myFile, 'rb+') as f:
				f.seek(-1,os.SEEK_END)	#f.truncate()
				f.write( json.dumps(appendData).replace('{', ',').encode() )	
			"""
			with open(myFile,'r+') as f: 
				f.seek(fileSize - 1)
				#f.seek(-1, os.SEEK_END)
				#f.seek(-1,2)
				#f.truncate()
				f.write( appendData )"""
	
	fileName = f'./logs/{today}-0dte-datalog.json'
	saveDataFile( SPX0DTEdayData, SPXLastData, fileName )

	if bln1dte :
		fileName = f'./logs/{today}-1dte-datalog.json'
		with open(fileName,'w') as f: 
			json.dump(SPX1DTEdayData, f)

	fileName = f'./logs/last-datalog.json'  #cheating on networking client-server.   the last update is always here
	with open(fileName,'w') as f: 
		json.dump(SPXLastData, f)

def appendData():
	global SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE, SPXLastData, skipPreMarket
	minute = getStrTime()
	if minute > 614 and minute < 630: return #Dont record the time frame where prices glitch
	if minute < 630 :
		skipPreMarket = (skipPreMarket + 1) % 15
		if skipPreMarket != 1 : return

	try:
		options = dp.getOptionsChain("SPX", 0)
		gex = dp.getGEX( options[1] )
		price = gex[0][dp.GEX_STRIKE] + ((gex[0][dp.GEX_CALL_BID] + gex[0][dp.GEX_CALL_ASK]) / 2)
		if SPXopenPrice == -1: SPXopenPrice = price
		gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
		#SPX0DTEdayData[getStrTime()] = {**{'price': price, 'data': gex}}
		SPX0DTEdayData[minute] = gex
		SPXLastData = {}
		SPXLastData[minute] = gex
		if gex == "": print('GEX Empty String')
		if skip1DTE == 0:
			options = dp.getOptionsChain("SPX", 1)
			gex = dp.getGEX( options[1] )
			gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
			SPX1DTEdayData[minute] = gex
		
		skip1DTE = (skip1DTE + 1) % 15
		save0dte(skip1DTE == 0)
	except Exception as error:
		print(f'AppendData - An error occoured: {error}')

def startDay():
	global blnRun, SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE
	try:  # In the event of an error, just start the day anyways......
		state = dp.getMarketHoursToday()
		print( state )
		if 'closed' in state['state'] : #Seems to not apply to sunday!!!
			#{'date': '2023-12-17', 'description': 'Market is closed', 'state': 'closed', 'timestamp': 1702808042, 'next_change': '07:00', 'next_state': 'premarket'}
			print( 'Market Closed Today')
			return
	except Exception as error:
		print(f'StartDay - An error occoured: {error}')
		
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
	#save0dte()
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

print("Running Version 3.0 More OVN Data")
schedule.every().day.at("00:00").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)

timer = dp.RepeatTimer(20, timerThread, daemon=True)
timer.start()
#now = datetime.datetime.now()
tmp = getStrTime()#(now.hour * 100) + now.minute
if (tmp > 0) and (tmp < 1300): 
	print('Late start to the day')
	startDay()
#startDay()

# Loop so that the scheduling task keeps on running all time.
while True: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )