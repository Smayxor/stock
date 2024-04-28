#This module intended to identify trade signals
import datapuller as dp
import heapq

DAY_RANGE, DAY_PUMP, DAY_DUMP = 0, 1, 2

def identifyKeyLevels(strikes):
	lenStrikes = len(strikes)
	
	price = dp.getPrice(ticker="SPX", strikes=strikes)
	
	#strikes = dp.shrinkToCount(strikes, price, 60)
	
	priceModulus = (price % 50)
	priceLower50 = price - priceModulus
	priceUpper50 = priceLower50 + 50
	priceBounds = [priceLower50, priceUpper50]
	
	hasValueList = [x for x in strikes if (x[dp.GEX_STRIKE] > price and x[dp.GEX_CALL_BID] > 0.3) or (x[dp.GEX_STRIKE] < price and x[dp.GEX_PUT_BID] > 0.3)]
	main5 = heapq.nlargest( 5, hasValueList, key=lambda x: x[dp.GEX_TOTAL_OI])
	
	mostCallOI = max(strikes, key=lambda i: i[dp.GEX_CALL_OI])[dp.GEX_CALL_OI]
	mostPutOI = max(strikes, key=lambda i: i[dp.GEX_PUT_OI])[dp.GEX_PUT_OI]
	mostCallPutOI = max( (mostCallOI, mostPutOI) )
	mostTotalOI = max(strikes, key=lambda i: i[dp.GEX_TOTAL_OI])[dp.GEX_TOTAL_OI]
	
	sumCallOI = sum( [x[dp.GEX_CALL_OI] for x in strikes] )
	sumPutOI = sum( [x[dp.GEX_PUT_OI] for x in strikes] )
	sumTotalOI = sum( [x[dp.GEX_CALL_OI] + x[dp.GEX_PUT_OI] for x in strikes] )
	
	averageCallOI = sumCallOI / lenStrikes
	averagePutOI = sumPutOI / lenStrikes
	averageTotalOI = sumTotalOI / lenStrikes
	
	strResult = ""
	straddles = []
	callWalls = []
	putWalls = []
	#print(1)
	for node in main5:
		strike = node
		#strike = next(x for x in strikes if x[dp.GEX_STRIKE] == node)
		#print(3)
		if (strike[dp.GEX_CALL_OI] > averageCallOI * 3 or strike[dp.GEX_CALL_OI] > mostCallOI * 0.7) and strike[dp.GEX_PUT_OI] < strike[dp.GEX_CALL_OI] * 0.5 :
			callWalls.append( node[dp.GEX_STRIKE] )
			strResult = f' CallWall {node[dp.GEX_STRIKE]} -' + strResult 
		elif (strike[dp.GEX_PUT_OI] > averagePutOI * 3 or strike[dp.GEX_PUT_OI] > mostPutOI * 0.7) and strike[dp.GEX_CALL_OI] < strike[dp.GEX_PUT_OI] * 0.5 :
			putWalls.append( node[dp.GEX_STRIKE] )
			strResult = f' PutWall {node[dp.GEX_STRIKE]} -' + strResult 
		elif strike[dp.GEX_TOTAL_OI] > averageTotalOI * 2 :
			straddles.append( node[dp.GEX_STRIKE] )
			strResult = f' Straddle {node[dp.GEX_STRIKE]} -' + strResult 
		
	i = 0
	while i < len(callWalls) :
		node = callWalls[i]
		if node + 5 in callWalls :
			callWalls.pop(i)
		else : i += 1
	i = 0
	while i < len(putWalls) :
		node = putWalls[i]
		if node - 5 in putWalls :
			putWalls.pop(i)
		else : i += 1
	
		#print(4)
	#print( [f'{node[dp.GEX_STRIKE]} -' for node in main5] )
	#print( strResult )
	
	dayType = DAY_RANGE
	if sumCallOI > sumPutOI * 1.4 : dayType = DAY_PUMP
	if sumPutOI > sumCallOI * 1.4 : dayType = DAY_DUMP
	
	return (priceBounds, dayType, straddles, putWalls, callWalls)
"""
Day 0 - ISP and NISP, Range Day.   Largest CallWall works
Day 1 - ISP and NISP and NISP, Range Day.  Play pump from ZeroG
Day 2 - Pump Day.   Chase unflagged CallWall.   30 points away from Fake-CallWall = Entry
Day 3 - Condor Day,  Filter out ISP and NISP next to each other
Day 5 - Only has CallWalls.   AverageOI Greater than usual.   Split PVN
Day 6 - SUCKS Crab Day
Day 12 - Large Gamma Imbalance - Fake Pump Day - Extreme Premium Imbalance
Day 13 - Only Straddle - Minimal Premium
Day 14 - Fake Dump - ISP Day
Day 15 - Faulty Data
Day 23 - ???
"""