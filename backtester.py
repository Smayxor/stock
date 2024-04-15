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
previousClose = 0
#for candle in candles: print( candle['date'] )

for file in fileList:
	gexData = dp.pullLogFile(file)
	end = file.replace('-0dte-datalog.json','')
	#start = str(datetime.datetime.strptime(end, '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
	#print( start, " - ", end )
	
	strikes = gexData[ next(iter(gexData)) ]
	#strikes = gexData[ next(t for t in gexData if float(t) > 630) ]
	openPrice = dp.getPrice("SPX", strikes)#firstStrike[dp.GEX_STRIKE] + ((firstStrike[dp.GEX_CALL_BID] + firstStrike[dp.GEX_CALL_ASK]) / 2)
	if previousClose == 0: previousClose = openPrice

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

	lowestPrice = 999999
	highestPrice = 0
	prices = [openPrice]
	#prices.append( openPrice )
	priceDif = 0
	
	prevData = {}
	
	lenData = len(gexData) - 2
	for time in gexData:
		minute = float( time )
		strikes = gexData[time]
		if minute < 630 and minute > 614 : continue
		
		price = dp.getPrice('SPX', strikes=strikes)
		prices.append( price )
		if price > highestPrice : highestPrice = price
		if price < lowestPrice : lowestPrice = price
		
		prevData[time] = strikes
		
		lastPrice = prices[-2]
		
		if callEntered == 0 and putEntered == 0:
			if 640 < minute < 700 :
				priceDif += prices[-1] - prices[-2]
					
			else :
				if priceDif < 5 : putEntered = 1
				if priceDif > 5 : callEntered = 1
		
		if callEntered == 1:
			#callStrike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - price - 20) )[dp.GEX_STRIKE]
			callStrike = min(strikes, key=lambda i: abs(i[dp.GEX_CALL_ASK] - 2) )[dp.GEX_STRIKE]
			tmpPrices = []
			for x in prevData:
				tmpPrices.append( next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)[dp.GEX_CALL_ASK] )
			callEntryPrice = min( tmpPrices )
			callEntered = 2
			#print( f'Price of {price} - Planning call {callStrike} @ ${callEntryPrice}' )
			
		if putEntered == 1:
			#putStrike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - price + 20) )[dp.GEX_STRIKE]
			putStrike = min(strikes, key=lambda i: abs(i[dp.GEX_PUT_ASK] - 2) )[dp.GEX_STRIKE]
			tmpPrices = []
			for x in prevData:
				tmpPrices.append( next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)[dp.GEX_PUT_ASK] )
			putEntryPrice = min( tmpPrices )
			putEntered = 2
			#print( f'Price of {price} - Planning put {putStrike} @ ${putEntryPrice}' )
			
		if callEntered == 2:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			ask = strike[dp.GEX_CALL_ASK]
			if ask <= callEntryPrice :
				callEntered = 3
				pnl -= callEntryPrice
				callExitPrice = callEntryPrice * 2
				print(f'{end} Entered {callStrike} Call for ${callEntryPrice} - {minute}')
		
		if putEntered == 2:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)
			ask = strike[dp.GEX_PUT_ASK]
			if ask <= putEntryPrice :
				putEntered = 3
				pnl -= putEntryPrice
				putExitPrice = putEntryPrice * 2
				print(f'{end} Entered {putStrike} Put for ${putEntryPrice} - {minute}')
		
		if callEntered == 3:		
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			bid = strike[dp.GEX_CALL_BID]
			if bid < callEntryPrice - 0.20 : callExitPrice = bid * 3
			if bid < 1 or bid >= callExitPrice or minute >= 1200:
				callEntered = 4
				tmp = min( (bid, callExitPrice) )  #Ensure correct Exit Price for conditions
				pnl += tmp
				print(f'Sold {callStrike} Call for {tmp} - {minute}')
			
		if putEntered == 3:	
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)
			bid = strike[dp.GEX_PUT_BID]
			if bid < putEntryPrice - 0.20 : putExitPrice = bid * 3
			if bid < 1 or bid >= putExitPrice or minute >= 1200:
				putEntered = 4
				tmp = min((bid, putExitPrice))
				pnl += tmp
				print(f'Sold {putStrike} Put for {tmp} - {minute}')
			
				
	previousClose = prices[-1]	

	if pnl < mostDown: mostDown = pnl
print(f'Total PnL ${round(pnl * 100, 2)},  most negative ${round(mostDown * 100, 2)}')
