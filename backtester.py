import ujson as json #usjon is json written in C
import requests
import datapuller as dp
import datetime
import random

ticker = 'SPX'
pnl = 0
mostDown = 0
allFiles = dp.pullLogFileList()
#print( allFiles )
fileList = [x for x in allFiles if ((ticker=='SPX') ^ ('SPY' in x))]
fileList.sort()
#fileList = [x for x in allFiles if 'SPY' in x]

#Grab price history for all days in range, and previous 30 so we can figure out ATR
firstFile = fileList[0]
firstDay = str(datetime.datetime.strptime(firstFile.replace('-datalog.json','').replace('SPY-',''), '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
lastFile = fileList[-1]
lastDay = lastFile.replace('-datalog.json','').replace('SPY-','')
candles = dp.getHistoryRange(ticker, firstDay, lastDay)

#for candle in candles: print( candle['date'] )

for file in fileList:
	gexData = dp.pullLogFile(file)
	end = file.replace('-datalog.json','').replace('SPY-','')
	#start = str(datetime.datetime.strptime(end, '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
	#print( start, " - ", end )
	
	openTime = next(iter(gexData))
	firstStrike = gexData[openTime]['data'][0]
	openPrice = firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)
	strikes = gexData[openTime]['data']

	callEntered = 0
	putEntered = 0
	callStrike = 0
	putStrike = 0
	callEntryPrice = 0
	putEntryPrice = 0
	callLowestPrice = 0
	putLowestPrice = 0
	callExitPrice = 0
	putExitPrice = 0
	callLowTime = 0
	putLowTime = 0

	#******************
	targets = dp.findKeyLevels( strikes, openPrice, targets=True )
	
	print( f'{end} OpenPrice ${openPrice} strikes {targets[0][dp.GEX_STRIKE]} and {targets[1][dp.GEX_STRIKE]}' )
	
	x = -1
	lenData = len(gexData) - 2
	for time in gexData:
		x += 1
		minute = time[:5]
		strikes = gexData[time]['data']
		firstStrike = strikes[0]
		price = firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)
		
		tmpCall = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - targets[0][dp.GEX_STRIKE]))
		callSideAsk = tmpCall[dp.GEX_CALL_ASK]
		tmpPut = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - targets[1][dp.GEX_STRIKE]))
		putSideAsk = tmpPut[dp.GEX_PUT_ASK]
	
		if callEntered == 1:
			strike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - callStrike))
			bid = strike[dp.GEX_CALL_BID]
			if putSideAsk < 0.30 or x == lenData :#or bid >= callExitPrice:
				callEntered = -1
				pnl += bid
				print(f'Sold {callStrike} Call for {bid}')
		if callEntered == 0:
			if x < lenData - 120 and callSideAsk <= 0.25 :
				strike = min(strikes, key=lambda i: abs(i[dp.GEX_CALL_ASK] - 3))
				callEntered = 1
				callEntryPrice = strike[dp.GEX_CALL_ASK]
				callExitPrice = 1
				callStrike = strike[dp.GEX_STRIKE]
				pnl -= callEntryPrice
				print(f'{end} Entered {callStrike} Call for ${callEntryPrice}')
		
		if putEntered == 1:
			strike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - putStrike))
			bid = strike[dp.GEX_PUT_BID]
			if callSideAsk < 0.30 or x == lenData :#or bid >= putExitPrice :
				putEntered = -1
				pnl += bid
				print(f'Sold {putStrike} put for {bid}')
		if putEntered == 0:
			if x < lenData - 120 and putSideAsk <= 0.25 :
				strike = min(strikes, key=lambda i: abs(i[dp.GEX_PUT_ASK] - 3))
				putEntered = 1
				putEntryPrice = strike[dp.GEX_PUT_ASK]
				putExitPrice = 0.5
				putStrike = strike[dp.GEX_STRIKE]
				pnl -= putEntryPrice
				print(f'{end} Entered {putStrike} Put for ${putEntryPrice}')
		

	if pnl < mostDown: mostDown = pnl
print(f'Total PnL ${round(pnl * 100, 2)},  most negative ${round(mostDown * 100, 2)}')
