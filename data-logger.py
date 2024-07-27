import datetime
import ujson as json #usjon is json written in C
import requests
import time
#import schedule
import datapuller as dp
import os
import tkinter as tk

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}

blnRun = False
blnSkipPrint = False
timer =  None
CurrentCalendar = None
SPXData = None

class DaysData():
	def __init__(self, ticker, dte, count):
		self.Ticker = ticker
		self.RecordDate = dte if '-' in dte else dp.getExpirationDate(self.Ticker, dte)
		print( dte, ' to ', self.RecordDate )
		self.OpenPrice = None
		self.StrikeCount = count
		self.FileName = f'./logs/{self.RecordDate}-0dte-datalog.json'
		self.LastDataFileName = f'./logs/last-datalog.json'
		self.Data = {}
		self.LastData = {}
		
		self.FoldLow = {}
		self.FoldHigh = {}
		self.FoldLowPrice = 9999999
		self.FoldHighPrice = 0
		self.FoldCount = 0
		self.FoldLastData = {}
		
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
			
	def addTime(self, minute):
		#print(f'4 - {minute} addTime start')
		if 614 < minute < 630 : 
			if self.FoldCount == 0 : return True
			self.FoldCount == 99999 # Make sure we separate OVN from RTH
		#EOD = minute >= 1300
		#if EOD : self.FoldCount == 99999
		#print(f'5 - {minute} addTime try')
		try:
			options = dp.getOptionsChain(self.Ticker, 0, date=self.RecordDate)
			if options is None : 
				print(f'{minute} - No options data')
				return
			#print(f'6 - Converting to my format')
			gex = dp.getGEX( options[1] )
			if self.OpenPrice is None :
				self.OpenPrice = dp.getPrice(self.Ticker, gex)
				print(f'OpenPrice assigned {self.OpenPrice}')
			#print(f'7 - Shrink to count')
			gex = dp.shrinkToCount(gex, self.OpenPrice, self.StrikeCount)
			price = dp.getPrice(self.Ticker, gex)
			self.FoldCount += 1
			#print(f'8 - Checking High Low')
			if price > self.FoldHighPrice :
				self.FoldHighPrice = price
				self.FoldHigh = gex
			if price < self.FoldLowPrice :
				self.FoldLowPrice = price
				self.FoldLow = gex
		
			candleLength = 180 if minute < 630 else 6
			blnWrite = self.FoldCount >= candleLength
			#print('6 - ', self.FoldCount , candleLength, blnWrite)
		
			self.FoldLastData = {}
			self.FoldLastData['final'] = blnWrite
			self.FoldLastData[minute] = self.FoldLow
			self.FoldLastData[minute+0.01] = self.FoldHigh
			#if EOD == False : # Record the Close Price
			self.FoldLastData[minute+0.02] = gex # The CurrentClose data
			self.FoldLastData[minute+0.03] = gex # Repeat data so it compatible with candles on client
				
			with open(self.LastDataFileName,'w') as f:  # Needs to write last price in its own file for Client
				json.dump(self.FoldLastData, f)

			if blnWrite :
				#print(f'7 - Writing {minute}')
				self.FoldCount = 0
				self.FoldHighPrice = 0
				self.FoldLowPrice = 9999999
				self.FoldLastData.pop( 'final', None ) # Signals Client that the Candle has ended
				self.FoldLastData.pop( minute+0.02, None ) # We dont want to commit this to the main file
				self.FoldLastData.pop( minute+0.03, None )
				self.Data.update( self.FoldLastData )
				blnGood = self.appendData( self.FoldLastData )
				if not blnGood is None : print(f'Error writing data - {minute}')

		except Exception as error:
			print( f'{minute} - Grab Data - {error}' )

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01)

def getToday():
	global testTime
	dateAndtime = str(datetime.datetime.now()).split(" ")	#2024-04-05 21:57:32.688823
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 100) + float(tmp[1]) + (float(tmp[2]) * 0.01)
	#testTime += 10
	#if testTime > 2400 : testTime = 0
	return (dateAndtime[0], minute)

intState = 0
lastDay = -1
def timerTask():
	global win, lblStatus, intState, SPXData, CurrentCalendar, lastDay
	tday = getToday()
	day = tday[0]
	minute = tday[1]
	if minute > 1500 :   #Lets just start reccording before the day even starts.  MUCH MORE OVN Data
		day = str(datetime.datetime.now() + datetime.timedelta(1)).split(" ")[0]
		minute = minute-2400

	#day = "2024-07-25"
	#print(f'1 - {day} TimerTask {minute}')
	if minute > 1300 :
		SPXData = None #Make extra certain we dont use old days
		win.title( f'{day} - EOD - {minute}')
		lblStatus.configure(text=f'{minute} EOD')
		return
	#print('2 - Minute adjustment')
	if lastDay != day :
		#print(f'*{lastDay}* not *{day}*')
		print(f'New day began {day}')
		try :
			print(f'Fetching new month data')
			if CurrentCalendar == None : CurrentCalendar = dp.getCalendar()
		except Exception as error :
			print(f'Fatal Calender API Failure')
			return
		print(f'Checking {day} if market is open')
		lastDay = day
		#month0dte = int(day.split('-')[1])
		#monthCurCal = CurrentCalendar['month']
		days = CurrentCalendar['days']['day']
		if next((x for x in days if x['date'] == day), None)['status'] == 'closed' :	
			print('Market is closed today')
			intState = -1
			SPXData = None #Make extra certain we dont use old days
			return
			
		intState = 1
		SPXData = DaysData( "SPX", day, 50 )
		print( f'{SPXData.RecordDate} - Day started' )
	
	win.title( f'{day} - Running - {minute}')
	if SPXData is None : return
	lblStatus.configure(text=f'{minute}')
	try:
		SPXData.addTime(minute)
	except Exception as error:
		print( f'{minute} Timerthread - {error}' )
	
def on_closing():
	global blnRun, timer
	blnRun = False
	timer.cancel()
	win.destroy()
	
def clickStart():
	global blnRun, timer
	blnRun = True
	print( timer )
	print( f'Timer active = {timer.is_alive()}' )
	if timer.is_alive() == False :
		timer = dp.RepeatTimer(5, timerTask, daemon=True)
		timer.start()
	
def clickStatus():
	pass
	
win = tk.Tk()
width, height = 360, 100
win.geometry(str(width) + "x" + str(height))
win.protocol("WM_DELETE_WINDOW", on_closing)

lblStatus = tk.Label(win, text="Running", width=20, anchor="w")
lblStatus.place(x=0, y=0)

tk.Button(win, text="Start", command=clickStart, width=10).place(x=0, y=30)
tk.Button(win, text="Status", command=clickStatus, width=10).place(x=0, y=60)

print("Running Version 6.0 GUI Mode + MAX OVN Data")

timer = dp.RepeatTimer(5, timerTask, daemon=True)
timer.start()

blnRun = False

tk.mainloop()