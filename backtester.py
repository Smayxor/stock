import ujson as json #usjon is json written in C
import requests
import datapuller as dp
import datetime

ticker = 'SPX'
pnl = 0
mostDown = 0
fileList = [x for x in dp.pullLogFileList() if ((ticker=='SPX') ^ ('SPY' in x))]
for file in fileList:
	gexData = dp.pullLogFile(file)
	end = file.replace('-datalog.json','')#.replace('SPY-','')
	start = str(datetime.datetime.strptime(end, '%Y-%m-%d') - datetime.timedelta(days=30)).split(' ')[0]
	#print( start, " - ", end )
	
	openTime = next(iter(gexData))
	openPrice = gexData[openTime]['price']
	strikes = gexData[openTime]['data']


	candles = dp.getHistoryRange(ticker, start, end)
	#{'date': '2023-10-30', 'open': 4139.39, 'high': 4177.47, 'low': 4132.94, 'close': 4166.82, 'volume': 0}
	endLen = len(candles)
	x = endLen - 2
	atr = 0
	totalCandles = 0
	while totalCandles < 14:
		candle = candles[x]
		atr += candle['high'] - candle['low']
		totalCandles += 1 
		x -= 1
	previousClose = candles[-2]['close']
	atr = atr / totalCandles

	fibHigh = previousClose + (atr * 0.236)
	fibLow = previousClose - (atr * 0.236)
	
	
	callEntered = 0
	putEntered = 0
	callStrike = 0
	putStrike = 0
	callEntryPrice = 0
	putEntryPrice = 0
	lowestCallPrice = 0
	lowestPutPrice = 0
	
	x = 0
	for time in gexData:
		x += 1
		minute = time[:5]
		if (callEntered == 1):
			for strike in gexData[time]['data']:
				if (strike[dp.GEX_STRIKE] == callStrike) :
					if strike[dp.GEX_CALL_BID] < lowestCallPrice: lowestCallPrice = strike[dp.GEX_CALL_BID]
					if ((strike[dp.GEX_CALL_BID] >= lowestCallPrice * 3) or (minute == '12:59')):
						pnl += strike[dp.GEX_CALL_BID]
						callEntered = -1
						print(f'{minute} Call sold at {strike[dp.GEX_CALL_BID]}')
						break
		if (callEntered == 0) and (gexData[time]['price'] < fibLow) and (x < 180):
			for strike in gexData[time]['data']:
				if 3 < strike[dp.GEX_CALL_ASK] < 5:
					callEntryPrice = strike[dp.GEX_CALL_ASK]
					callStrike = strike[dp.GEX_STRIKE]
					pnl -= callEntryPrice
					lowestCallPrice = callEntryPrice
					callEntered = 1
					print(f'{minute} Call entered at strike {callStrike} cost {callEntryPrice}')
					break

		if (putEntered == 1):
			for strike in gexData[time]['data']:
				if (strike[dp.GEX_STRIKE] == putStrike):
					if strike[dp.GEX_PUT_BID] < lowestPutPrice : lowestPutPrice = strike[dp.GEX_PUT_BID]
					if ((strike[dp.GEX_PUT_BID] >= lowestPutPrice * 3) or (minute == '12:59')):
						pnl += strike[dp.GEX_PUT_BID]
						putEntered = -1
						print(f'{minute} Put sold at {strike[dp.GEX_PUT_BID]}')
						break
		if (putEntered == 0) and (gexData[time]['price'] > fibHigh) and (x < 180):
			for strike in gexData[time]['data']:
				if 3 < strike[dp.GEX_PUT_ASK] < 5:
					putEntryPrice = strike[dp.GEX_PUT_ASK]
					putStrike = strike[dp.GEX_STRIKE]
					pnl -= putEntryPrice
					lowestPutPrice = putEntryPrice
					putEntered = 1
					print(f'{minute} Put entered at strike {putStrike} cost {putEntryPrice}')
					break
	if pnl < mostDown: mostDown = pnl
print(f'Total PnL ${round(pnl * 100, 2)},  most negative ${round(mostDown * 100, 2)}')
"""
	break
	
	candles = dp.getHistoryRange(ticker, start, end)
	#{'date': '2023-10-30', 'open': 4139.39, 'high': 4177.47, 'low': 4132.94, 'close': 4166.82, 'volume': 0}
	endLen = len(candles)
	x = endLen - 2
	atr = 0
	totalCandles = 0
	while totalCandles < 14:
		candle = candles[x]
		atr += candle['high'] - candle['low']
		totalCandles += 1 
		x -= 1
	previousClose = candles[-2]['close']
	atr = atr / totalCandles

	fibHigh = previousClose + (atr * 0.236)
	fibLow = previousClose - (atr * 0.236)
	priceState = 0
	hits = 0
	for minute in gexData:
		#print( gexData[minute] )  #{'price': 4401.415873377881, 'data': [[4275.0,
		price = gexData[minute]['price']

		if price > fibHigh :
			if priceState != 1: hits += 1
			priceState = 1
		elif price < fibLow :
			if priceState != -1: hits += 1
			priceState = -1
		#else :
		#	priceState = 0

	print( f'{end} Total hits {hits}' )
"""