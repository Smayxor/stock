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
SPXData = None

class DaysData():
	def __init__(self, ticker, dte, count, startTime, foldTime):
		myTime = getToday()
		minute = myTime[1]
		self.Ticker = ticker
		self.RecordDate = dp.getExpirationDate(self.Ticker, dte)
		print( 'Dates pulled ', myTime[0], self.RecordDate )
		self.OpenPrice = None
		self.StrikeCount = count
		self.FileName = f'./logs/{self.RecordDate}-0dte-datalog.json'
		self.LastDataFileName = f'./logs/last-datalog.json'
		self.Data = {}
		self.LastData = {}
		
		self.FoldTime = foldTime
		self.FoldLow = {}
		self.FoldHigh = {}
		self.FoldLowPrice = 9999999
		self.FoldHighPrice = 0
		self.FoldCount = 0 # if minute < foldTime else -1
		self.FoldLastData = {}
		
		try:  #Check for existing data
			tmpData = json.load(open(self.FileName))
			firstStrike = tmpData[next(iter(tmpData))]
			self.OpenPrice = dp.getPrice(self.Ticker, firstStrike)
			self.Data.update( tmpData )
		except Exception as error:
			pass #print( f'init error - {error}' )
		
		self.grabData(minute, False)

	def appendData(self, gex):
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
			print( f'AppendData Error - {error}' )
			
	def grabData(self, minute, EOD):
		if 614 < minute < 630 : 
			if self.FoldCount == 0 : return True
			self.FoldCount == 99999 # Make sure we separate OVN from RTH
		if EOD : self.FoldCount == 99999
		
		try:
			options = dp.getOptionsChain(self.Ticker, 0, date=self.RecordDate)
			#print( f'Response headers - { options[2]}' )
			gex = dp.getGEX( options[1] )
			if self.OpenPrice == None :
				self.OpenPrice = dp.getPrice(self.Ticker, gex)
				print(f'OpenPrice assigned {self.OpenPrice}')
			gex = dp.shrinkToCount(gex, self.OpenPrice, self.StrikeCount)
			price = dp.getPrice(self.Ticker, gex)
			self.FoldCount += 1

			if price > self.FoldHighPrice :
				self.FoldHighPrice = price
				self.FoldHigh = gex
				#print(f'{minute} - assigned High Price {price}')
			if price < self.FoldLowPrice :
				self.FoldLowPrice = price
				self.FoldLow = gex
				#print(f'{minute} - assigned Low Price {price}')
		
			candleLength = 120 if minute < 630 else 6
			blnWrite = self.FoldCount >= candleLength
		
			self.FoldLastData = {}
			self.FoldLastData['final'] = blnWrite
			self.FoldLastData[minute] = self.FoldLow
			self.FoldLastData[minute+0.01] = self.FoldHigh
			if EOD == False : # Record the Close Price
				self.FoldLastData[minute+0.02] = gex # The CurrentClose data
				self.FoldLastData[minute+0.03] = gex # Repeat data so it compatible with candles on client
				
				#print(  [ dp.getPrice("SPX", v) for k, v in self.FoldLastData.items() if k != 'final' ]  )
				
				#print('Appending Current Price {dp.getPrice("SPX", gex)}')

			#print( EOD, [k for k, v in self.FoldLastData.items()] )
			with open(self.LastDataFileName,'w') as f:  # Needs to write last price in its own file for Client
				json.dump(self.FoldLastData, f)

			if blnWrite :
				self.FoldCount = 0
				self.FoldHighPrice = 0
				self.FoldLowPrice = 9999999
				self.FoldLastData.pop( 'final', None ) # Signals Client that the Candle has ended
				self.FoldLastData.pop( minute+0.02, None ) # We dont want to commit this to the main file
				self.FoldLastData.pop( minute+0.03, None )
				self.Data.update( self.FoldLastData )
				self.appendData( self.FoldLastData )

		except Exception as error:
			print( f'Grab Data - {error}' )
		
	def addTime(self):
		myTime = getToday()
		minute = myTime[1]
		result = minute > 1300
		try:
			self.grabData(minute, result)
		except Exception as error:
			print(f'Addtime error - {error}')
		return not result

def startDay():
	global blnRun, CurrentCalendar, SPXData
	try :
		today = getToday()[0]
		if CurrentCalendar == None : CurrentCalendar = dp.getCalendar()
		month0dte = int(today.split('-')[1])
		monthCurCal = CurrentCalendar['month']
		if month0dte != monthCurCal : CurrentCalendar = dp.getCalendar()
		days = CurrentCalendar['days']['day']
		if next((x for x in days if x['date'] == today), None)['status'] == 'closed' :	
			print('Market is closed today')
			return
	except Exception as error:
		print( f'Calendar issue' )
		return
	
	blnRun = True
	SPXData = DaysData( "SPX", 0, 50, 0,  630 )
	print( f'{SPXData.RecordDate} - Day started' )

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01)

def getToday():
	dateAndtime = str(datetime.datetime.now()).split(" ")	#2024-04-05 21:57:32.688823
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 100) + float(tmp[1]) + (float(tmp[2]) * 0.01)
	return (dateAndtime[0], minute)

def timerThread():
	global blnRun, SPXData
	if not blnRun : return
	try:
		blnRun = SPXData.addTime()
	except Exception as error:
		print( f'TimerThread error - {error}' )
	if blnRun == False : print('Finished saving options data')
		
print("Running Version 4.0 OOPS + Faster with Candles")
schedule.every().day.at("00:00").do(startDay)  #Currently set to PST
#schedule.every().day.at("13:00").do(endDay)   # Can be handled through the main Timer

timer = dp.RepeatTimer(5, timerThread, daemon=True)
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