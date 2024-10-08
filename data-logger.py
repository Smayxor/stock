import datetime
import ujson as json #usjon is json written in C
import requests
import time
#import schedule
import datapuller as dp
import os
import tkinter as tk
import asyncio

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
FILE_PATH = "C:/logs/"
CurrentCalendar = None
SPXData = None

class DaysData():
	def __init__(self, ticker, dte, count):
		self.Ticker = ticker
		self.RecordDate = dte if '-' in dte else dp.getExpirationDate(self.Ticker, dte)
		print( dte, ' to ', self.RecordDate )
		self.OpenPrice = None
		self.StrikeCount = count
		self.FileName = f'{FILE_PATH}{self.RecordDate}-0dte-datalog.json'
		self.LastDataFileName = f'{FILE_PATH}last-datalog.json'
		self.Data = {}
		self.LastData = {}
		
		self.FoldLow = {}
		self.FoldHigh = {}
		self.FoldLowPrice = 9999999
		self.FoldHighPrice = 0
		self.FoldCount = 0
		self.FoldLastData = {}
		
		self.Sess, self.Req, self.Prepped = dp.sessionSetValues(ticker, self.RecordDate)
		
		try:  #Check for existing data
			tmpData = json.load(open(self.FileName))
			firstStrike = tmpData[next(iter(tmpData))]
			self.OpenPrice = dp.getPrice(self.Ticker, firstStrike)
			self.Data.update( tmpData )
		except Exception as error:
			pass #print( f'init error - {error}' )

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
			return "error"
		return None
			
	async def addTime(self, minute):
		verbosePrint(1)
		if 614 < minute < 630 : 
			if self.FoldCount == 0 : return True
			self.FoldCount == 99999 # Make sure we separate OVN from RTH
		#EOD = minute >= 1300
		#if EOD : self.FoldCount == 99999
		verbosePrint(2)
		try:
			#options = dp.getOptionsChains(self.Ticker, 0, date=self.RecordDate)
			options = await dp.sessionGetOptionsChain(self.Sess, self.Req, self.Prepped)
			
			verbosePrint(3)
			if options is None : 
				print(f'{minute} - No options data')
				return
			verbosePrint(4)
			gex = dp.getGEX( options )
			verbosePrint(5)
			if self.OpenPrice is None :
				self.OpenPrice = dp.getPrice(self.Ticker, gex)
				print(f'OpenPrice assigned {self.OpenPrice}')
			verbosePrint(6)
			gex = dp.shrinkToCount(gex, self.OpenPrice, self.StrikeCount)
			verbosePrint(7)
			price = dp.getPrice(self.Ticker, gex)
			verbosePrint(8)
			self.FoldCount += 1
			verbosePrint(9)
			if price > self.FoldHighPrice :
				self.FoldHighPrice = price
				self.FoldHigh = gex
			if price < self.FoldLowPrice :
				self.FoldLowPrice = price
				self.FoldLow = gex
			verbosePrint(10)
			candleLength = 180 if minute < 615 else 8
			blnWrite = self.FoldCount >= candleLength
			verbosePrint(11)
			self.FoldLastData = {}
			self.FoldLastData['final'] = blnWrite
			self.FoldLastData[minute] = self.FoldLow
			self.FoldLastData[minute+0.01] = self.FoldHigh
			#if EOD == False : # Record the Close Price
			self.FoldLastData[minute+0.02] = gex # The CurrentClose data
			self.FoldLastData[minute+0.03] = gex # Repeat data so it compatible with candles on client
			verbosePrint(12)
			with open(self.LastDataFileName,'w') as f:  # Needs to write last price in its own file for Client
				json.dump(self.FoldLastData, f)
			verbosePrint(13)
			if blnWrite :
				verbosePrint(14)
				self.FoldCount = 0
				self.FoldHighPrice = 0
				self.FoldLowPrice = 9999999
				verbosePrint(15)
				self.FoldLastData.pop( 'final', None ) # Signals Client that the Candle has ended
				self.FoldLastData.pop( minute+0.02, None ) # We dont want to commit this to the main file
				self.FoldLastData.pop( minute+0.03, None )
				verbosePrint(16)
				self.Data.update( self.FoldLastData )
				verbosePrint(17)
				blnGood = self.appendData( self.FoldLastData )
				verbosePrint(18)
				if not blnGood is None : print(f'Error writing data - {minute}')
				verbosePrint(19)
		except Exception as error:
			print( f'{minute} - Grab Data - {error}' )
		verbosePrint(20)

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01)

def getToday():
	tempo = datetime.datetime.today()# + datetime.timedelta(1) #For testing purposes
	minute = (tempo.hour * 100) + tempo.minute + (tempo.second * 0.01)
	if minute > 1800 :
		tempo = tempo + datetime.timedelta(1)
		minute = minute - 2400
	todaysDate = f'{tempo.year}-{tempo.month:02d}-{tempo.day:02d}'
	return (todaysDate, minute, tempo.month)

lastDay = -1
TIMER_INTERVAL = 1000 * 5
def timerTask():
	global win, lblStatus, SPXData, CurrentCalendar, lastDay
	win.after(TIMER_INTERVAL, timerTask)  #Called at start of timerTask() to prevent errors from stopping this thing
	verbosePrint( 'Timer Start' )
	tday = getToday()
	day = tday[0]
	minute = tday[1]
	verbosePrint( tday )
	if minute > 1300 :
		SPXData = None #Make extra certain we dont use old days
		win.title( f'{day} - EOD - {minute}')
		lblStatus.configure(text=f'{minute} EOD')
		return
	else:
		win.title( f'{day}  Running  {minute}')
		lblStatus.configure(text=f'{minute} SPXData = {SPXData}')
	verbosePrint( 'Compare days' )
	if lastDay != day :
		print(f'New day began {day}')
		lastDay = day
		try :
			print(f'Fetching new month data')
			CurrentCalendar = dp.getCalendar()
			if tday[2] != int(CurrentCalendar.get('month', -1)) : print('New month, start timer at midnight?')
			
		except Exception as error :
			print(f'Fatal Calender API Failure')
			return
		print(f'Checking {day} if market is open')
		days = CurrentCalendar['days']['day']
		
		dummy = {'status': 'closed'} #Should mean we have a new month!!!!
		testDay = next((x for x in days if x['date'] == day), dummy)
		
		status = testDay.get('status', 'closed')
		if status == 'closed' :	
			print('Market is closed today')
			SPXData = None #Make extra certain we dont use old days
			return

		SPXData = DaysData( "SPX", day, 50 )
		print( f'{SPXData.RecordDate} - Day started' )
	verbosePrint( 'Checking SPXData' )
	if SPXData is None : return
	verbosePrint( 'Adding time' )
	try:
		asyncio.run( SPXData.addTime(minute) )
	except Exception as error:
		print( f'{minute} Timerthread - {error}' )
	verbosePrint( 'Completed timer task' )
	
def on_closing():
	win.destroy()
	
def clickStart():
	global blnVerbose, intVerbose
	blnVerbose = not blnVerbose
	print( blnVerbose, intVerbose )
	
def clickStatus():
	pass
	
blnVerbose = False
intVerbose = -1
def verbosePrint( val ):
	global blnVerbose, intVerbose
	intVerbose = val
	if blnVerbose : print( intVerbose )
	
win = tk.Tk()
width, height = 360, 100
win.geometry(str(width) + "x" + str(height))
win.protocol("WM_DELETE_WINDOW", on_closing)

lblStatus = tk.Label(win, text="Running", width=20, anchor="w")
lblStatus.place(x=0, y=0)

tk.Button(win, text="Start", command=clickStart, width=10).place(x=0, y=30)
tk.Button(win, text="Status", command=clickStatus, width=10).place(x=0, y=60)

print("Running Version 6.0 GUI Mode + MAX OVN Data")

#timer = dp.RepeatTimer(5, timerTask, daemon=True)
#timer.start()
win.after(TIMER_INTERVAL, timerTask)

tk.mainloop()

#python -m trace --trace YOURSCRIPT.py