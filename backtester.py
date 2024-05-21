import ujson as json #usjon is json written in C
import requests
import datapuller as dp
import datetime
import signals as sig

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


daysTR = {}
TRs = json.load(open(f'./logs/TR.json'))
def calcATR(day):
	prevClose = -1
	ATR = 0
	for k, v in TRs.items(): 
		dayAsNumber = int( k.replace('-', '') )
		if day in k:
			#result = sorted( TRs, key=lambda pd: int( pd.replace('-', '') ) )[:14]
			listDays = []
			for xk, xv in reversed(TRs.items()):
				xDN = int( xk.replace('-', '') )
				if dayAsNumber - xDN > 0 : 
					listDays.append( xDN )
					if prevClose == -1 : prevClose = xv[1]
					ATR += xv[0]
				if len( listDays ) == 14 : break
			while len(listDays) != 14:
				listDays.append(50)
				ATR += 50
			ATR = ATR / 14
			#print(dayAsNumber, ' - ', ATR, prevClose)
			return (ATR, prevClose)

wins = 0
losses = 0
for file in fileList:
	gexData = dp.pullLogFile(file)
	end = file.replace('-0dte-datalog.json','')
	#start = str(datetime.datetime.strptime(end, '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
	
	firstTime = next(iter(gexData))
	strikes = gexData[firstTime]
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
	
	#prices.append( openPrice )
	priceDif = 0
	firstTime = min( gexData.keys(), key=lambda i: abs(631 - float(i)))  #Data sucks at 630, and could catch time before at data fault
	strikes = gexData[firstTime]
	sigs = sig.identifyKeyLevels(strikes)
	strat = sig.SignalDataRelease(firstTime=firstTime, strikes=strikes, deadprice=0.30)
	flags = []
	lastFlag = 0
	lenData = len(gexData) - 1
	x = -1
	openPrice = 0
	for time in gexData:
		x += 1
		minute = float( time )
		strikes = gexData[time]
		if minute < 630 and minute > 614 : continue
		
		price = dp.getPrice('SPX', strikes=strikes)
		flag = strat.addTime(minute, strikes)
		flags.append( flag )
		if flag != 0 : lastFlag = flag 
		"""
		if x == lenData :
			ovnRange = int(strat.OVNH - strat.OVNL)
			dayRange = int(strat.High - strat.Low)
			mHigh = max( (strat.High, strat.OVNH) )
			mLow = min( (strat.Low, strat.OVNL) )
			totalRange = int(mHigh - mLow)
			#if totalRange > 50 or totalRange < 30:
			
			if strat.LargestCandle > 15 :
				print( f'{end} - OVN {ovnRange} - Day {dayRange} - Total {totalRange} - LargestWick {strat.LargestCandle}' )
			
		continue
		"""
		if openPrice == 0 :
			if minute > 629 :
				openPrice = price	
				sigs = sig.identifyKeyLevels(strikes)
				#print(f'{end} - Price ${price} - Targets - {sigLevels}')
			else: continue
		
		if minute < 700:
			if lastFlag == 1 and callEntered == 0 : callEntered = 1
			if lastFlag == -1  and putEntered == 0 : putEntered = 1


		if callEntered == 1:
			#callStrike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - price - 20) )[dp.GEX_STRIKE]
			strike = min(strikes, key=lambda i: abs(i[dp.GEX_CALL_ASK] - 2) )
			callStrike = strike[dp.GEX_STRIKE]
			callEntryPrice = strike[dp.GEX_CALL_ASK]
			callEntered = 2
			#print( f'Price of {price} - Planning call {callStrike} @ ${callEntryPrice}' )
			
		if putEntered == 1:
			#putStrike = min(strikes, key=lambda i: abs(i[dp.GEX_STRIKE] - price + 20) )[dp.GEX_STRIKE]
			strike = min(strikes, key=lambda i: abs(i[dp.GEX_PUT_ASK] - 2) )
			putStrike = strike[dp.GEX_STRIKE]
			putEntryPrice = strike[dp.GEX_PUT_ASK]
			putEntered = 2
			#print( f'Price of {price} - Planning put {putStrike} @ ${putEntryPrice}' )
			
		if callEntered == 2:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			ask = strike[dp.GEX_CALL_ASK]
			if ask <= callEntryPrice :
				callEntered = 3
				pnl -= callEntryPrice
				callExitPrice = callEntryPrice + 1
				print(f'{end} Entered {callStrike} Call for ${callEntryPrice} - {minute}')
		
		if putEntered == 2:
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)
			ask = strike[dp.GEX_PUT_ASK]
			if ask <= putEntryPrice :
				putEntered = 3
				pnl -= putEntryPrice
				putExitPrice = putEntryPrice + 1
				print(f'{end} Entered {putStrike} Put for ${putEntryPrice} - {minute}')
		
		if callEntered == 3:		
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == callStrike)
			bid = strike[dp.GEX_CALL_BID]
			#if bid < callEntryPrice - 0.20 : callExitPrice = bid * 3
			if bid >= callExitPrice or minute >= 1200 :#or bid <= callEntryPrice - 0.5: #bid < 0.5 or bid >= callExitPrice
				callEntered = 4
				tmp = min( (bid, callExitPrice) )  #Ensure correct Exit Price for conditions
				pnl += tmp
				print(f'Sold {callStrike} Call for {tmp} - {minute}')
				if bid >= callExitPrice : 
					wins += 1
					print('***********************************************WINNER**************************************')
				else: losses += 1
			
		if putEntered == 3:	
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == putStrike)
			bid = strike[dp.GEX_PUT_BID]
			#if bid < putEntryPrice - 0.20 : putExitPrice = bid * 3
			if bid >= putExitPrice or minute >= 1200 :#or bid <= putEntryPrice - 0.5: #bid < 0.5 or bid >= putExitPrice
				putEntered = 4
				tmp = min((bid, putExitPrice))
				pnl += tmp
				print(f'Sold {putStrike} Put for {tmp} - {minute}')
				if bid >= putExitPrice : 
					wins += 1
					print('***********************************************WINNER**************************************')
				else: losses += 1		
		

	if pnl < mostDown: mostDown = pnl
print(f'Total PnL ${round(pnl * 100, 2)},  most negative ${round(mostDown * 100, 2)}')
print(f'Winners : {wins} - Losers {losses}')
#for day, candle in daysTR.items() : print( f'{day} - {candle}' )
#with open(f'./logs/TR.json', 'w') as f:
#	json.dump(daysTR, f)