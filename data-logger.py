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
		self.FoldCount = 0 if minute < foldTime else -1
		self.FoldLastData = {}
		
		try:  #Check for existing data
			tmpData = json.load(open(self.FileName))
			firstStrike = tmpData[next(iter(tmpData))]
			self.OpenPrice = dp.getPrice(self.Ticker, firstStrike)
			self.Data.update( tmpData )
		except Exception as error:
			pass #print( f'init error - {error}' )
		
		self.grabData(minute)

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
			
			with open(self.LastDataFileName,'w') as f: 
				json.dump(gex, f)
		except Exception as error:
			print( f'AppendData Error - {error}' )
			
	def grabData(self, minute):
		try:
			options = dp.getOptionsChain(self.Ticker, 0, date=self.RecordDate)
			gex = dp.getGEX( options[1] )
			if self.OpenPrice == None :
				self.OpenPrice = dp.getPrice(self.Ticker, gex)
				print(f'OpenPrice assigned {self.OpenPrice}')
			gex = dp.shrinkToCount(gex, self.OpenPrice, self.StrikeCount)
			
			if minute > self.FoldTime :
				self.Data[minute] = gex
				self.appendData(gex)
			else : #Fold Data
				if self.FoldCount != -1 : return
				self.FoldCount += 1
				price = dp.getPrice(self.Ticker, gex)
				if price > self.FoldHighPrice :
					self.FoldHighPrice = price
					self.FoldHigh = gex
					#print(f'{minute} - assigned High Price {price}')
				if price < self.FoldLowPrice :
					self.FoldLowPrice = price
					self.FoldLow = gex
					#print(f'{minute} - assigned Low Price {price}')
			
				if self.FoldCount == 20 :
					self.FoldCount = 0
					self.FoldHighPrice = 0
					self.FoldLowPrice = 9999999
					self.FoldLastData = {}
					self.FoldLastData[minute] = self.FoldLow
					self.FoldLastData[minute+0.01] = self.FoldHigh
					self.Data.update( self.FoldLastData )
					self.appendData( self.FoldLastData )
					if minute > 610 : self.FoldCount = -1  # Ensures we grab the last folded recording

		except Exception as error:
			print( f'Grab Data - {error}' )
		
	def addTime(self):
		myTime = getToday()
		minute = myTime[1]
		#print( f'Fetching {minute}')
		self.grabData(minute)

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
	
def endDay():
	global blnRun, SPXData
	if not blnRun : return
	blnRun = False
	today = getToday()[0] # str(datetime.date.today()).split(":")[0]
	print('Finished saving options data')

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
		SPXData.addTime()
	except Exception as error:
		print( f'TimerThread error - {error}' )
		
print("Running Version 4.0 OOPS + Folded OVN Data")
schedule.every().day.at("00:00").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)

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