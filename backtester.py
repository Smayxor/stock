import ujson as json #usjon is json written in C
import requests
import datapuller as dp
import datetime
import random

ticker = 'SPX'
pnl = 0
mostDown = 0
allFiles = dp.pullLogFileList()

fileList = [x for x in allFiles if '0dte' in x]
fileList.sort()
#print( fileList )
#Grab price history for all days in range, and previous 30 so we can figure out ATR
firstFile = fileList[0]
lastFile = fileList[-1]
lastDay = lastFile.replace('-0dte-datalog.json','')

#for candle in candles: print( candle['date'] )

for file in fileList:
	gexData = dp.pullLogFile(file)
	end = file.replace('-0dte-datalog.json','')
	#start = str(datetime.datetime.strptime(end, '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
	#print( start, " - ", end )
	
	strikes = gexData[ next(iter(gexData)) ]
	openPrice = dp.getPrice("SPX", strikes)#firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)

	callEntered = 0
	putEntered = 0
	callStrike = 0
	putStrike = 0
	callEntryPrice = 0
	putEntryPrice = 0
	callLowestPrice = 990
	putLowestPrice = 990
	callExitPrice = 0
	putExitPrice = 0
	callLowTime = 0
	putLowTime = 0

	#******************
	targets = dp.findKeyLevels( strikes, openPrice, targets=True )
	
	callStrike = max( [x for x in targets[0] if x[dp.GEX_STRIKE] > openPrice], key=lambda i: i[dp.GEX_CALL_OI])[dp.GEX_STRIKE]
	putStrike = max([x for x in targets[1] if x[dp.GEX_STRIKE] < openPrice], key=lambda i: i[dp.GEX_PUT_OI])[dp.GEX_STRIKE]
	#callStrike = max(targets[0], key=lambda i: i[dp.GEX_CALL_OI])[dp.GEX_STRIKE]
	#putStrike = max(targets[1], key=lambda i: i[dp.GEX_PUT_OI])[dp.GEX_STRIKE]
	print( f'{end} - Call ${callStrike}, Put ${putStrike}')
	lowestPrice = openPrice
	highestPrice = openPrice
	
	x = -1
	lenData = len(gexData) - 2
	for time in gexData:
		minute = float( time )
		strikes = gexData[time]
		price = dp.getPrice('SPX', strikes=strikes)
		
		if price > highestPrice : highestPrice = price
		if price < lowestPrice : lowestPrice = price
		
		if minute < 630 :
			if minute > 614 : continue 
			tmp = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)[dp.GEX_CALL_BID]
			if callLowestPrice > tmp : callLowestPrice = tmp + 0.05
			tmp = next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)[dp.GEX_PUT_BID]
			if putLowestPrice > tmp : putLowestPrice = tmp + 0.05
			continue
		
		if callEntered == 1:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			bid = strike[dp.GEX_CALL_BID]
			if bid >= callExitPrice or minute >= 1259:# or bid <= callLowestPrice :
				callEntered = -1
				pnl += bid
				if minute >= 1259 : print( 'EOD HODL!!!!' )
				print(f'Sold {callStrike} Call for {bid}')
				
		if callEntered == 0:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			ask = strike[dp.GEX_CALL_ASK]
			if minute > 700 and highestPrice - lowestPrice > 10 : #ask <= 0.30 and :
				strike = min(strikes, key=lambda i: abs(i[dp.GEX_CALL_ASK] - 2) )
				callStrike = strike[dp.GEX_STRIKE]
				callEntered = 1
				callEntryPrice = strike[dp.GEX_CALL_ASK]
				callExitPrice = callEntryPrice + 1
				callLowestPrice = callEntryPrice * 0.5
				pnl -= callEntryPrice
				print(f'{end} Entered {callStrike} Call for ${callEntryPrice}')
			

	if pnl < mostDown: mostDown = pnl
print(f'Total PnL ${round(pnl * 100, 2)},  most negative ${round(mostDown * 100, 2)}')
