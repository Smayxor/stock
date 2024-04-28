#This module intended to identify trade signals
import datapuller as dp
import heapq

DAY_RANGE, DAY_PUMP, DAY_DUMP = 0, 1, 2

def identifyKeyLevels(strikes):
	lenStrikes = len(strikes)
	
	price = dp.getPrice(ticker="SPX", strikes=strikes)
	priceModulus = (price % 50)
	priceLower50 = price - priceModulus
	priceUpper50 = priceLower50 + 50
	priceBounds = [priceLower50, priceUpper50]
	"""
	for strike in strikes:
		strike[dp.GEX_CALL_OI] += strike[dp.GEX_CALL_VOLUME]
		strike[dp.GEX_PUT_OI] += strike[dp.GEX_PUT_VOLUME]
		strike[dp.GEX_TOTAL_OI] = strike[dp.GEX_CALL_OI] + strike[dp.GEX_PUT_OI] """
	
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
		if (strike[dp.GEX_CALL_OI] > averageCallOI * 3 or strike[dp.GEX_CALL_OI] > mostCallOI * 0.8) and strike[dp.GEX_PUT_OI] < strike[dp.GEX_CALL_OI] * 0.5 :
			callWalls.append( node[dp.GEX_STRIKE] )
			strResult = f' CallWall {node[dp.GEX_STRIKE]} -' + strResult 
		elif (strike[dp.GEX_PUT_OI] > averagePutOI * 3 or strike[dp.GEX_PUT_OI] > mostPutOI * 0.8) and strike[dp.GEX_CALL_OI] < strike[dp.GEX_PUT_OI] * 0.5 :
			putWalls.append( node[dp.GEX_STRIKE] )
			strResult = f' PutWall {node[dp.GEX_STRIKE]} -' + strResult 
		elif strike[dp.GEX_TOTAL_OI] > averageTotalOI * 2 :
			straddles.append( node[dp.GEX_STRIKE] )
			strResult = f' Straddle {node[dp.GEX_STRIKE]} -' + strResult 
			
			
		#print(4)
	#print( [f'{node[dp.GEX_STRIKE]} -' for node in main5] )
	print( strResult )
	
	dayType = DAY_RANGE
	if sumCallOI > sumTotalOI * 0.6 : dayType = DAY_PUMP
	if sumPutOI > sumTotalOI * 0.6 : dayType = DAY_DUMP
	
	return (priceBounds, dayType, straddles, putWalls, callWalls)