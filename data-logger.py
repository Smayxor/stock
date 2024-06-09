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
CurrentCalendar = None
SPX0DTEdayData = {}
SPX1DTEdayData = {}
SPXLastData = {}
SPXopenPrice = -1 #Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned
skip1DTE = 0
skipPreMarket = 0
lowSPX = None
highSPX = None

GMEData = {}

def save0dte(bln1dte, thisDate):
	global SPX0DTEdayData, SPX1DTEdayData, SPXLastData, GMEData
	#today = getToday()[0] #str(datetime.date.today()).split(":")[0]
	
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
	
	fileName = f'./logs/{thisDate}-0dte-datalog.json'
	saveDataFile( SPX0DTEdayData, SPXLastData, fileName )



	if bln1dte :
		fileName = f'./logs/{thisDate}-1dte-datalog.json'
		with open(fileName,'w') as f: 
			json.dump(SPX1DTEdayData, f)

	fileName = f'./logs/last-datalog.json'  #cheating on networking client-server.   the last update is always here
	with open(fileName,'w') as f: 
		json.dump(SPXLastData, f)
		
	fileName = f'./logs/{thisDate}-GME.json'
	with open(fileName,'w') as f: 
		json.dump(GMEData, f)

def appendData():
	global SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE, SPXLastData, skipPreMarket, lowSPX, highSPX, SPX0DTEDate, SPX1DTEDate, GMEDate, GMEData
	myTime = getToday()
	minute = myTime[1] #getStrTime()
	if minute > 614 and minute < 630: return #Dont record the time frame where prices glitch

	try:
		options = dp.getOptionsChain("SPX", 0, date=SPX0DTEDate)
		gex = dp.getGEX( options[1] )
		price = dp.getPrice('SPX', gex) #gex[0][dp.GEX_STRIKE] + ((gex[0][dp.GEX_CALL_BID] + gex[0][dp.GEX_CALL_ASK]) / 2)
		if SPXopenPrice == -1: 
			#Should LOAD FILE to GET the OpenPrice.   In case service is started, computer reboots/crashes,  then program is resumed
			SPXopenPrice = price
		gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
		if gex == "": print('GEX Empty String')
		
		#**********************************************************************************
		if minute < 630 : #Special Premarket folded logging
			skipPreMarket = (skipPreMarket + 1) % 15
			#print( f'Minute {minute} - {skipPreMarket} - Skip {skipPreMarket != 1}' )
			
			if lowSPX == None :
				lowSPX = gex
				highSPX = gex
					
			lowPrice = dp.getPrice("SPX", lowSPX)
			highPrice = dp.getPrice("SPX", highSPX)
			
			if price < lowPrice : lowSPX = gex
			if price > highPrice : highSPX = gex
					
			if skipPreMarket == 14 :
				SPX0DTEdayData[minute] = lowSPX
				SPX0DTEdayData[minute + 0.01] = highSPX
				
				SPXLastData = {}
				SPXLastData[minute] = lowSPX
				SPXLastData[minute + 0.01] = highSPX
				
				save0dte( False, thisDate = myTime[0])
				lowSPX = None
			return
		#***********************************************************************************

		#Normal logging during day
		SPX0DTEdayData[minute] = gex
		SPXLastData = {}
		SPXLastData[minute] = gex		
		
		if skip1DTE == 0:
			options = dp.getOptionsChain("SPX", 1, date=SPX1DTEDate)
			gex = dp.getGEX( options[1] )
			gex = dp.shrinkToCount(gex, SPXopenPrice, 50)  #Must be centered around same price all day long!!!
			SPX1DTEdayData[minute] = gex
		
		if minute > 600:  #GME prolly wont change OVN
			options = dp.getOptionsChain("GME", 0, date=GMEDate)
			gex = dp.getGEX( options[1] )
			GMEData[minute] = gex
		
		skip1DTE = (skip1DTE + 1) % 15
		save0dte(skip1DTE == 0, thisDate = myTime[0])		
	except Exception as error:
		print(f'{minute} AppendData - An error occoured: {error}')
		#state = dp.getMarketHoursToday()   #DONT DO THIS.   If network connection fails, unhandled exception stops timer
		#print( f'During Error State - {state}' )

def startDay():
	global blnRun, SPX0DTEdayData, SPX1DTEdayData, SPXopenPrice, skip1DTE, skipPreMarket, lowSPX, highSPX, SPX0DTEDate, SPX1DTEDate, CurrentCalendar, GMEDate, GMEData
	
	try :
		#state = dp.getMarketHoursToday()
		today = getToday()[0]
		if CurrentCalendar == None : CurrentCalendar = dp.getCalendar()
		month0dte = int(today.split('-')[1])
		monthCurCal = CurrentCalendar['month']
		if month0dte != monthCurCal : CurrentCalendar = dp.getCalendar()
		days = CurrentCalendar['days']['day']
		if next((x for x in days if x['date'] == today), None)['status'] == 'closed' :	
			print('Market is closed today')
			return
		#for d in days:
		#	if d['status'] == 'closed' : print(d)
	except Exception as error:
		print( error )
		return
	
	blnRun = True
	SPX0DTEdayData = {}
	SPXopenPrice = -1
	SPX1DTEdayData = {}
	GMEData = {}
	skip1DTE = 0
	skipPreMarket = 0
	lowSPX = None
	highSPX = None
	SPX0DTEDate = dp.getExpirationDate('SPX', 0)
	SPX1DTEDate = dp.getExpirationDate('SPX', 1)
	GMEDate = dp.getExpirationDate('GME', 0)
	print(SPX0DTEDate, SPX1DTEDate, GMEDate)
    
	try:
		fileName = f'./logs/{SPX0DTEDate}-0dte-datalog.json'
		tmpData = json.load(open(f'{fileName}'))
		firstStrike = tmpData[next(iter(tmpData))]
		tmpPrice = dp.getPrice("SPX",firstStrike)
		SPXopenPrice = tmpPrice
		SPX0DTEdayData.update( tmpData )
	except Exception as error:
		print( error )

	print( f'{SPX0DTEDate} - Day started + GME' )
	
def endDay():
	global blnRun, SPX0DTEdayData, SPX1DTEdayData
	if not blnRun : return
	blnRun = False
	today = getToday()[0] # str(datetime.date.today()).split(":")[0]
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
	return (now.hour * 100) + now.minute + (now.second * 0.01)

def getToday():
	dateAndtime = str(datetime.datetime.now()).split(" ")	#2024-04-05 21:57:32.688823
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 100) + float(tmp[1]) + (float(tmp[2]) * 0.01)
	return (dateAndtime[0], minute)

def timerThread():
	global blnRun
	if not blnRun : return
	appendData()

print("Running Version 3.0 More OVN Data")
schedule.every().day.at("00:00").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)

timer = dp.RepeatTimer(20, timerThread, daemon=True)
timer.start()
tmp = getToday()[1]
if (tmp > 0) and (tmp < 1300): 
	print('Late start to the day')
	startDay()

# Loop so that the scheduling task keeps on running all time.
while True: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )