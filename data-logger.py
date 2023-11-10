import datetime
import ujson as json #usjon is json written in C
import requests
import threading
import time
import schedule
#import pandas as pd
#import numpy as np
import datapuller as dp
import socket

#DataLogger, schedules a timer to begin recording data when market opens 6:30 am PST,  using Tradier API

init = json.load(open('apikey.json'))
TRADIER_ACCESS_CODE = init['TRADIER_ACCESS_CODE']
TRADIER_HEADER = {'Authorization': f'Bearer {TRADIER_ACCESS_CODE}', 'Accept': 'application/json'}
blnRun = True
INTERVAL = 60 #Time in seconds between recordings
openPrice = 0.0
dayData = {}
#test = 0
openPrice = 0  #Used so we can ShrinkToCount around the same price value, all day long.  Keeps strike indices alligned


def appendData():
	global test
	price = dp.getQuote('SPX')
	options = dp.getOptionsChain("SPX", 0)
	gex = dp.getGEX( options[1] )
	gex = dp.shrinkToCount(gex, openPrice, 100)  #Must be centered around same price all day long!!!
	dayData[f'{getStrTime()}'] = {**{'price': price, 'data': gex}}
#	test += 1
#	if test == 5: endDay()
	threading.Timer(INTERVAL, minuteTimerThread).start()
	#schedule.every(1).minutes.do(minuteTimerThread)

def startDay():
	global openPrice, dayData, blnRun, openPrice
	blnRun = True
	print( "Day started" )
	openPrice = dp.getQuote('SPX')
	appendData()
	
def endDay():
	global blnRun, dayData
	blnRun = False
	today = str(datetime.date.today()).split(":")[0]
	fileName = f'./logs/{today}-datalog.json'
	with open(fileName,'w') as f: 
		json.dump(dayData, f)

def getStrTime(): return str(datetime.datetime.now()).split(' ')[1].split('.')[0]

def minuteTimerThread():
	global openPrice, dayData, blnRun
	if not blnRun : return
	appendData()
	
def getPandasOptionsChain(ticker, price):	#Unused, being kept in case I wanna mess with pandas someday.  Converting Pandas to Dict and storing in a file is a terrible data structure
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





def serverThread():  #Was thinking about a file server, so data-logger.py could be ran on a different machine
	# Create a socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Bind the socket to a port
	sock.bind(('', 8080))
	# Listen for connections
	sock.listen(1)
	# Accept a connection
	client, addr = sock.accept()
	# Receive the filename
	filename = client.recv(1024)
	# Create a file with the same name
	with open(filename, 'wb') as f:
		# Receive the file data
		while True:
			data = client.recv(1024)
			if not data:
				break
				f.write(data)

				# Close the connection
				client.close()

#	if __name__ == '__main__':
#		main()



print("Running Version 2.0 ArrayOfTuples - NoPandas")
schedule.every().day.at("06:30").do(startDay)  #Currently set to PST
schedule.every().day.at("13:00").do(endDay)
#schedule.every().day.at("07:00").do(endDay)
#startDay()
# Loop so that the scheduling task keeps on running all time.
while blnRun: # Checks whether a scheduled task is pending to run or not
	schedule.run_pending()
	time.sleep(1)
print( 'Finished logging data' )