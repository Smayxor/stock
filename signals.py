#This module intended to identify trade signals
import datapuller as dp
import heapq

DAY_RANGE, DAY_PUMP, DAY_DUMP, DAY_CRAZY, DAY_CONDOR, DAY_BREACH = 0, 1, 2, 3, 4, 5
#fitness(x) = 1 / (sum_of_all_positive_metrics_mentioned_above - sum_of_all_negative_metrics_mentioned_above)
"""time in trade
percentage of port / percentage of budget
number of trades taken
number of trades won
avg gain per trade
stdev of avg gain per trade
avg loss per trade
stdev of avg loss per trade
avg drawdown
stdev of avg drawdown
avg time in drawdown
stdev of avg time in drawdown"""

def identifyKeyLevels(strikes):
	lenStrikes = len(strikes)
	price = dp.getPrice(ticker="SPX", strikes=strikes)
	#strikes = dp.shrinkToCount(strikes, price, 60)
	
	priceModulus = (price % 50)
	priceLower50 = price - priceModulus
	priceUpper50 = priceLower50 + 50
	priceBounds = [priceLower50, priceUpper50]
	
	hasValueList = [x for x in strikes if (x[dp.GEX_STRIKE] > price and x[dp.GEX_CALL_BID] > 0.5) or (x[dp.GEX_STRIKE] < price and x[dp.GEX_PUT_BID] > 0.5)]
	mainNodes = heapq.nlargest( 10, hasValueList, key=lambda x: x[dp.GEX_TOTAL_OI])
	#print( [x[dp.GEX_STRIKE] for x in main5] )
	mostCallOI = max(strikes, key=lambda i: i[dp.GEX_CALL_OI])[dp.GEX_CALL_OI]
	mostPutOI = max(strikes, key=lambda i: i[dp.GEX_PUT_OI])[dp.GEX_PUT_OI]
	mostCallPutOI = max( (mostCallOI, mostPutOI) )
	mostTotalOI = max(strikes, key=lambda i: i[dp.GEX_TOTAL_OI])[dp.GEX_TOTAL_OI]
	
	totalOTMCallPremium = sum( [x[dp.GEX_CALL_OI] * x[dp.GEX_CALL_BID] for x in strikes if x[dp.GEX_STRIKE] > price] )
	totalOTMPutPremium = sum( [x[dp.GEX_PUT_OI] * x[dp.GEX_PUT_BID] for x in strikes if x[dp.GEX_STRIKE] < price] )
	#print( f'{int(totalOTMCallPremium):,}' , f'{int(totalOTMPutPremium):,}'  )
	
	sumCallOI = sum( [x[dp.GEX_CALL_OI] for x in strikes] )
	sumPutOI = sum( [x[dp.GEX_PUT_OI] for x in strikes] )
	sumTotalOI = sum( [x[dp.GEX_CALL_OI] + x[dp.GEX_PUT_OI] for x in strikes] )
	
	averageCallOI = sumCallOI / lenStrikes
	averagePutOI = sumPutOI / lenStrikes
	averageTotalOI = sumTotalOI / lenStrikes
	
	straddles = []
	callWalls = []
	putWalls = []
	zeroG = dp.calcZeroGEX( strikes )
	straddles.append( zeroG )
	
	lastPutVolume = 0
	for x in reversed(strikes):
		putVolume = x[dp.GEX_PUT_VOLUME]
		#if x[dp.GEX_STRIKE] == 5170 or x[dp.GEX_STRIKE] == 5165 : print( f'{x[dp.GEX_STRIKE]} - {putVolume}' )
		if lastPutVolume > 300 and lastPutVolume * 0.2 > putVolume :#and putVolume < 50 :
			callWalls.append( x[dp.GEX_STRIKE] )
			break
		lastPutVolume = putVolume
	
	for strike in mainNodes:
		if (strike[dp.GEX_CALL_OI] > averageCallOI * 2.5 or strike[dp.GEX_CALL_OI] > mostCallOI * 0.7) and strike[dp.GEX_PUT_OI] < strike[dp.GEX_CALL_OI] * 0.4 :
			callWalls.append( strike[dp.GEX_STRIKE] )
		elif (strike[dp.GEX_PUT_OI] > averagePutOI * 2.5 or strike[dp.GEX_PUT_OI] > mostPutOI * 0.7) and strike[dp.GEX_CALL_OI] < strike[dp.GEX_PUT_OI] * 0.4 :
			putWalls.append( strike[dp.GEX_STRIKE] )
		elif strike[dp.GEX_TOTAL_OI] > averageTotalOI * 2 :
			straddles.append( strike[dp.GEX_STRIKE] )
	#print( straddles, callWalls, putWalls )
	creditSpreads = 0
	i = 0 # Trim the CCS and PCS nodes to show outter node
	while i < len(callWalls) :
		node = callWalls[i]
		if node + 5 in callWalls :
			callWalls.pop(i)
			creditSpreads += 1
		else : i += 1
	i = 0
	while i < len(putWalls) :
		node = putWalls[i]
		if node - 5 in putWalls :
			putWalls.pop(i)
			creditSpreads += 1
		else : i += 1
	
	gexPolarity = [(x[dp.GEX_STRIKE], x[dp.GEX_TOTAL_GEX] >= 0) for x in strikes if abs(x[dp.GEX_STRIKE] - price) < 100]
	polaritySwitches = 0
	for i in range(1, len(gexPolarity) - 1) :
		node = gexPolarity[i][0]
		plus = gexPolarity[i][1]
		nextPlus = gexPolarity[i+1][1]
		lastPlus = gexPolarity[i-1][1]
		
		if plus != lastPlus : polaritySwitches += 1
		if (lastPlus == nextPlus) and (plus != lastPlus) and node not in straddles : straddles.append( node )
			
	#print(f'Polarity Switches {polaritySwitches}')

	#print( gexPolarity )
	
	dayType = DAY_RANGE
	#print( f'{sumCallOI} - {sumPutOI}')
	if sumCallOI > sumPutOI * 1.4 : dayType = DAY_BREACH
	if sumPutOI > sumCallOI * 1.4 : dayType = DAY_BREACH
	if creditSpreads == 2 : dayType = DAY_CONDOR
	if polaritySwitches > 4 : dayType = DAY_CRAZY
	#1d EXP Move calced by looking at Forward Volatility
	
	#print( '2 - ', straddles, putWalls, callWalls)
	return (priceBounds, dayType, straddles, putWalls, callWalls)

def OLDidentifyKeyLevels(strikes):
	lenStrikes = len(strikes)
	
	price = dp.getPrice(ticker="SPX", strikes=strikes)
	
	#strikes = dp.shrinkToCount(strikes, price, 60)
	
	priceModulus = (price % 50)
	priceLower50 = price - priceModulus
	priceUpper50 = priceLower50 + 50
	priceBounds = [priceLower50, priceUpper50]
	
	hasValueList = [x for x in strikes if (x[dp.GEX_STRIKE] > price and x[dp.GEX_CALL_BID] > 0.3) or (x[dp.GEX_STRIKE] < price and x[dp.GEX_PUT_BID] > 0.3)]
	main5 = heapq.nlargest( 5, hasValueList, key=lambda x: x[dp.GEX_TOTAL_OI])
	#print( [x[dp.GEX_STRIKE] for x in main5] )
	mostCallOI = max(strikes, key=lambda i: i[dp.GEX_CALL_OI])[dp.GEX_CALL_OI]
	mostPutOI = max(strikes, key=lambda i: i[dp.GEX_PUT_OI])[dp.GEX_PUT_OI]
	mostCallPutOI = max( (mostCallOI, mostPutOI) )
	mostTotalOI = max(strikes, key=lambda i: i[dp.GEX_TOTAL_OI])[dp.GEX_TOTAL_OI]
	
	sumCallOI = sum( [x[dp.GEX_CALL_OI] for x in strikes] )
	sumPutOI = sum( [x[dp.GEX_PUT_OI] for x in strikes] )
	sumTotalOI = sum( [x[dp.GEX_CALL_OI] + x[dp.GEX_PUT_OI] for x in strikes] )
	#print(1)
	averageCallOI = sumCallOI / lenStrikes
	averagePutOI = sumPutOI / lenStrikes
	averageTotalOI = sumTotalOI / lenStrikes
	#print(2)
	#strResult = ""
	straddles = []
	callWalls = []
	putWalls = []
	zeroG = dp.calcZeroGEX( strikes )
	straddles.append( zeroG )
	#print(1)
	for strike in main5:
		if (strike[dp.GEX_CALL_OI] > averageCallOI * 2.5 or strike[dp.GEX_CALL_OI] > mostCallOI * 0.7) and strike[dp.GEX_PUT_OI] < strike[dp.GEX_CALL_OI] * 0.4 :
			callWalls.append( strike[dp.GEX_STRIKE] )
			#strResult = f' CallWall {strike[dp.GEX_STRIKE]} -' + strResult 
		elif (strike[dp.GEX_PUT_OI] > averagePutOI * 2.5 or strike[dp.GEX_PUT_OI] > mostPutOI * 0.7) and strike[dp.GEX_CALL_OI] < strike[dp.GEX_PUT_OI] * 0.4 :
			putWalls.append( strike[dp.GEX_STRIKE] )
			#strResult = f' PutWall {strike[dp.GEX_STRIKE]} -' + strResult 
		elif strike[dp.GEX_TOTAL_OI] > averageTotalOI * 2 :
			straddles.append( strike[dp.GEX_STRIKE] )
			#strResult = f' Straddle {strike[dp.GEX_STRIKE]} -' + strResult 
	
	creditSpreads = 0
	i = 0 # Trim the CCS and PCS nodes to show outter node
	while i < len(callWalls) :
		node = callWalls[i]
		if node + 5 in callWalls :
			callWalls.pop(i)
			creditSpreads += 1
		else : i += 1
	i = 0
	while i < len(putWalls) :
		node = putWalls[i]
		if node - 5 in putWalls :
			putWalls.pop(i)
			creditSpreads += 1
		else : i += 1
	
	gexPolarity = [(x[dp.GEX_STRIKE], x[dp.GEX_TOTAL_GEX] >= 0) for x in strikes if abs(x[dp.GEX_STRIKE] - price) < 100]
	polaritySwitches = 0
	for i in range(1, len(gexPolarity) - 1) :
		node = gexPolarity[i][0]
		plus = gexPolarity[i][1]
		nextPlus = gexPolarity[i+1][1]
		lastPlus = gexPolarity[i-1][1]
		
		if plus != lastPlus : polaritySwitches += 1
		if (lastPlus == nextPlus) and (plus != lastPlus) and node not in straddles : straddles.append( node )
			
	#print(f'Polarity Switches {polaritySwitches}')

	#print( gexPolarity )
	
	dayType = DAY_RANGE
	if sumCallOI > sumPutOI * 1.4 : dayType = DAY_BREACH
	if sumPutOI > sumCallOI * 1.4 : dayType = DAY_BREACH
	if creditSpreads == 2 : dayType = DAY_CONDOR
	if polaritySwitches > 4 : dayType = DAY_CRAZY
	#1d EXP Move calced by looking at Forward Volatility
	
	return (priceBounds, dayType, straddles, putWalls, callWalls)




def findPeaksAndValleys( prices ):
	lenavgs = len( prices )
	highs = []
	lows = []
	last = prices[0]
	high = 0
	low = 0
	def checkNextHigh(index):
		#last = index + 30 if index + 30 < lenavgs else lenavgs
		last = index + 30
		if last > lenavgs : return False
		for i in range(index, last):
			if prices[i] > prices[index] : return False
		return True
	def checkNextLow(index):
		#last = index + 30 if index + 30 < lenavgs else lenavgs
		last = index + 30
		if last > lenavgs : return False
		for i in range(index, last):
			if prices[i] < prices[index] : return False
		return True

	for i in range( 1, lenavgs ) :
		if prices[i] > prices[high] and checkNextHigh(i):
			highs.append(i)
			high = i
			low = i
		elif prices[i] < prices[low] and checkNextLow(i):
			lows.append(i)
			low = i
			high = i
		else:
			pass
	return (lows, highs)

class Signal:	
	def __init__(self, firstTime, strikes, deadprice):
		self.deadprice = deadprice
		
		#price = dp.getPrice("SPX", strikes)
		self.OVNH = 0
		self.OVNL = 99999
		self.OpenPrice = -1
		self.Low = -1
		self.High = -1
		self.Prices = []
		self.PrevData = {}
		self.PrevDataTimes = []
		self.PrevData[firstTime] = strikes
		price = dp.getPrice("SPX", strikes)
		self.PreMarket = True
		#self.allPositions = sigs[2] + sigs[3] + sigs[4]
		self.callTimes = [[x[dp.GEX_STRIKE], -1] for x in strikes if (x[dp.GEX_CALL_BID] > deadprice) and (x[dp.GEX_STRIKE] % 5 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		self.putTimes = [[x[dp.GEX_STRIKE], -1] for x in strikes if (x[dp.GEX_PUT_BID] > deadprice) and (x[dp.GEX_STRIKE] % 5 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		
		self.LargestCandle = 0
	def addTime(self, minute, strikes):
		price = dp.getPrice("SPX", strikes)
		self.Prices.append(price)
		self.PrevDataTimes.append( minute )
		self.PrevData[minute] = strikes	
		lastPriceIndex = len(self.Prices)-1
		if minute < 631 : 
			if price < self.OVNL : self.OVNL = price
			if price > self.OVNH : self.OVNH = price
			
			if len(self.Prices) > 1:
				wick = abs(self.Prices[lastPriceIndex] - self.Prices[lastPriceIndex-1])
				if wick > self.LargestCandle : self.LargestCandle = wick
			return price
		
		if self.PreMarket:# Fill list of contracts with OVNL and OVNH data
			self.PreMarket = False
			self.OpenPrice = price
			self.Low = price
			self.High = price
			for c in self.callTimes :
				ovnl = 99999
				ovnh = 0
				for prevStrikes in self.PrevData.values() :
					bid = next((x[dp.GEX_CALL_BID] for x in prevStrikes if x[dp.GEX_STRIKE] == c[0]), None)
					if bid == None :
						ovnl = -1
						ovnh = -1
						break
					if bid > ovnh : ovnh = bid
					if bid < ovnl : ovnl = bid
				c.append( ovnl )
				c.append( ovnh )
			for p in self.putTimes :
				ovnl = 99999
				ovnh = 0
				for prevStrikes in self.PrevData.values() :
					bid = next((x[dp.GEX_PUT_BID] for x in prevStrikes if x[dp.GEX_STRIKE] == p[0]), None)
					if bid == None : 
						ovnl = -1
						ovnh = -1
						break
					if bid > ovnh : ovnh = bid
					if bid < ovnl : ovnl = bid
				p.append( ovnl )
				p.append( ovnh )	
			#print( 'calls ', self.callTimes, '\nputs ', self.putTimes )
		if price < self.Low : self.Low = price
		if price > self.High : self.High = price
				
		""" #Set Values for each contract when price reaches X
		for c in [c for c in self.callTimes if c[1] == -1] :
			bid = next((x[dp.GEX_CALL_BID] for x in strikes if x[dp.GEX_STRIKE] == c[0]), None)
			if bid == None : 
				c = [f'Missing\r{c[0]}', lastPriceIndex]
				continue
			if bid <= self.deadprice : c[1] = lastPriceIndex
		for p in [p for p in self.putTimes if p[1] == -1] :
			bid = next((x[dp.GEX_PUT_BID] for x in strikes if x[dp.GEX_STRIKE] == p[0]), None)
			if bid == None : 
				p = [f'Missing\r{p[0]}', lastPriceIndex]
				continue
			if bid <= self.deadprice : p[1] = lastPriceIndex
		"""
		#strike =  next((x for x in strikes if x[dp.GEX_STRIKE] == roundedPrice), None)
		#if strike == None :
		#	print(f'{roundedPrice} could not be found')
		#	return price
		
		#roundedPrice = price - (price % 5)
		def testContract( o, cp ):
			bid = next((x[cp] for x in strikes if x[dp.GEX_STRIKE] == o[0]), None)#
			if bid == None : 
				o = [f'Missing\r{o[0]}', lastPriceIndex]
				return
			if bid > o[3] : o[3] = bid
			if bid <= o[3] * self.deadprice :
				txt = f'{"{:.0%}".format(bid / o[3])} - {o[0]}'
				o[1] = lastPriceIndex if abs(price - o[0]) < 3 else -2  #Only show flags when SPX Spot Price is near Strike Price
				o[0] = txt
		for c in [c for c in self.callTimes if c[1] == -1] : testContract( c, dp.GEX_CALL_BID )
		for p in [p for p in self.putTimes if p[1] == -1] : testContract( p, dp.GEX_PUT_BID )
		
		return price
			
class SignalTemplate(Signal): #Blank Signal example
	def __init__(self, firstTime, strikes, deadprice):
		super().__init__(firstTime, strikes, deadprice)
	def addTime(self, minute, strikes):
		price = super().addTime(minute, strikes)
		x = len(self.Prices) - 1
		#price = self.Prices[x]
		
class SignalDPT(Signal):
	def __init__(self, firstTime, strikes, deadprice):
		super().__init__(firstTime, strikes, deadprice)
		self.lastOptionIndex = 0
		self.lastModulusIndex = 0
		self.bullFlag = 0
		self.callTimes = [[x[dp.GEX_STRIKE], -1] for x in strikes if (x[dp.GEX_CALL_BID] > deadprice) and (x[dp.GEX_STRIKE] % 25 == 0)]
		self.putTimes = [[x[dp.GEX_STRIKE], -1] for x in strikes if (x[dp.GEX_PUT_BID] > deadprice) and (x[dp.GEX_STRIKE] % 25 == 0)]

	def addTime(self, minute, strikes):
		super().addTime(minute, strikes)
		
		x = len(self.Prices) - 1
		price = self.Prices[x]
		if abs((price % 25) - 12.5) > 9: self.lastModulusIndex = x#Store index of last time price neared price%25
		#print(f'Price {price} - abs {abs((price % 25) - 12.5)}')
		
		for strike in strikes :
			for c in self.callTimes:
				if c[1] == -1 and c[0] == strike[dp.GEX_STRIKE] and strike[dp.GEX_CALL_BID] <= self.deadprice: 
					c[1] = x
					self.lastOptionIndex = x
					self.bullFlag = 1
			for p in self.putTimes:
				if p[1] == -1 and p[0] == strike[dp.GEX_STRIKE] and strike[dp.GEX_PUT_BID] <= self.deadprice: 
					p[1] = x
					self.lastOptionIndex = x
					self.bullFlag = -1
	
		result = (self.lastOptionIndex == x and x - self.lastModulusIndex < 5) \
			  or (self.lastModulusIndex == x and x - self.lastOptionIndex < 5)
		return self.bullFlag if result else 0

class Signal2x50(Signal):
	def __init__(self, firstTime, strikes, deadprice):
		super().__init__(firstTime, strikes, deadprice)
		self.pickNodes(strikes)
		self.FindNodes = True

	def pickNodes(self, strikes):
		self.FindNodes = False
		strike = next(x for x in strikes if x[dp.GEX_STRIKE] == self.Upper50)
		self.callTimes = [[self.Upper50, 0, strike[dp.GEX_CALL_BID], strike[dp.GEX_CALL_BID]]]
		strike = next(x for x in strikes if x[dp.GEX_STRIKE] == self.Lower50)
		self.putTimes = [ [self.Lower50, 0, strike[dp.GEX_PUT_BID], strike[dp.GEX_PUT_BID]]]
		#print( [x[0] for x in self.callTimes], [x[0] for x in self.putTimes] )
		
	def addTime(self, minute, strikes):
		price = super().addTime(minute, strikes)
		x = len(self.Prices) - 1
		
		if self.OpenPrice > -1 and self.FindNodes : self.pickNodes(strikes)

		result = 0
		for c in self.callTimes:
			strike = next((x for x in strikes if x[dp.GEX_STRIKE] == c[0]), None)
			if strike == None: continue
			bid = strike[dp.GEX_CALL_BID]
			
			if bid > c[3] : c[3] = bid
			if bid < c[2] : 
				c[2] = bid
				if c[3] < c[2] * 2 : c[3] = c[2]
			if not (0.2 < c[3]) : continue
			if bid <= c[3] * 0.5 : 
				result = 1
				c[1] = x
				c[3] = bid
		
		for p in self.putTimes:
			strike = next((x for x in strikes if x[dp.GEX_STRIKE] == p[0]), None)
			if strike == None: continue
			#if minute < 635 and strike[dp.GEX_STRIKE] == 4850 : print( f'Low {p[2]} - High {p[3]}')
			bid = strike[dp.GEX_PUT_BID]
			
			if bid > p[3] : p[3] = bid
			if bid < p[2] : 
				p[2] = bid
				if p[3] < p[2] * 2 : p[3] = p[2]
			if not (0.2 < p[3]) : continue
			if bid <= p[3] * 0.5 :
				#if strike[dp.GEX_STRIKE] == 5225 : print( f'Minute {minute} - Low {p[2]} - High {p[3]}')
				result = -1
				p[1] = x
				p[3] = bid
		
		return result

class SignalOVN(Signal):
	def __init__(self, firstTime, strikes, deadprice):
		super().__init__(firstTime, strikes, deadprice)
		self.Low = self.OVNL
		self.High = self.OVNH
	def addTime(self, minute, strikes):
		price = super().addTime(minute, strikes)
		
		x = len(self.Prices) - 1
		if minute < 630 : return 0
		if len( self.Prices ) < 10 : return 0 # No Premarket Data
		
		blnUnder = True
		blnOver = True
		for y in range( x-10, x-1):
			prePrice = self.Prices[y]
			blnUnder = blnUnder and (prePrice < self.OVNH)
			blnOver = blnOver and (prePrice > self.OVNL)
			
		if blnUnder and price >= self.OVNH : return -1
		if blnOver and price <= self.OVNL : return 1
		return 0


class SignalDataRelease(Signal):
	def __init__(self, firstTime, strikes, deadprice):
		super().__init__(firstTime, strikes, deadprice)
		self.FindNodes = True
		self.lowPre530 = 99999
		self.highPre530 = 0
		self.low530 = 99999
		self.high530 = 0
		self.lowAfter = 99999
		self.highAfter = 0
		self.TrendDirection = 0
		self.MidPoint = 0
		#self.result = 0
		
	def getContractOVNLowHigh(self, strikeStrike, call=True):
		element = dp.GEX_CALL_BID if call else dp.GEX_PUT_BID
		low, high = 9999, 0
		for minute, strikes in self.PrevData.items():
			strike = next(x for x in strikes if x[dp.GEX_STRIKE] == strikeStrike)
			bid = strike[element]
			if bid < low : low = bid
			if bid > high : high = bid
		return [strikeStrike, low, high]
	
	def addTime(self, minute, strikes):
		price = super().addTime(minute, strikes)
		x = len(self.Prices) - 1
		result = 0
		
		if minute < 530 : #Before Data Release
			if self.lowPre530 > price : self.lowPre530 = price
			if self.highPre530 < price : self.highPre530 = price
		elif minute < 540 :  #Data release
			if self.low530 > price : self.low530 = price
			if self.high530 < price : self.high530 = price
		elif minute < 630 : #Before OpenPrice
			if self.lowAfter > price : self.lowAfter = price
			if self.highAfter < price : self.highAfter = price
		elif self.FindNodes :
			self.FindNodes = False
			pre = (self.highPre530 - self.lowPre530) // 1
			drh = (self.high530 - self.highPre530) // 1
			drl = (self.low530 - self.lowPre530) // 1
			#print(f'Pre {self.lowPre530} x {self.highPre530}  - DR {self.low530} x {self.high530} ')
			maxDR = max((abs(drh), abs(drl)))
			#print( f'PreRange {pre} - DataRelase {drl} x {drh} ')
			#if maxDR > 16 : IsDataRelease
			#if maxDR < -16 : IsDataRelease
			self.TrendDirection = -1 if abs(price - self.OVNH) > (price - self.OVNL) else 1
			self.MidPoint = ((self.OVNH + self.OVNL) / 2) + (self.TrendDirection * 2)
			if self.OVNH - self.OVNL < 20 :
				self.TrendDirection = 0
			#print( f'Trend {self.TrendDirection}' )
		else :
			if price > self.OVNH + 9 : 
				result = -1
				#print(f'Buy Put - OVNH {self.OVNH} - Price {price}')
				self.OVNH = 999999
			if price < self.OVNL - 9 :
				result = 1
				#print(f'Buy Call - OVNL {self.OVNL} - Price {price}')
				self.OVNL = 0
			if self.TrendDirection == 1 and price < self.MidPoint :
				result = 1
				self.TrendDirection = 0
				#print(f'Trendy Call - MidPoint{self.MidPoint} - Price {price}')
			if self.TrendDirection == -1 and price > self.MidPoint :
				result = -1
				self.TrendDirection = 0
				#print(f'Trendy Put - MidPoint{self.MidPoint} - Price {price}')
		
		#if result != 0 : print( minute, ' ', result )
		
		return result


#strike = next((x for x in strikes if x[dp.GEX_STRIKE] == self.Upper50), None)
#https://studylib.net/doc/26075953/recognizing-over-50-candlestick-patterns-with-python-by-c
#EMA = Closing price * multiplier + EMA (previous day) * (1-multiplier). The multiplier is calculated using the formula 2 / (number of observations +1)
#EMA_1 = close_curr * [2 / (20 + 1)] + EMA_prev * [1 - [2 / (20 + 1)]]
"""
Day 78 -  ATM Both 50% = scalp
		  ATM 30% = scalp
		  20 points away 3100cp = 10% Put Enter Put, 10% call Exit put
Day 77 - 5300cp,  50% scalp Call until OVNH.
		 At 5300c OVNH = Enter Put, Exit at 2x
		 5320cp =  5320c 60% OVNL = Buy Call, Exit at 50% 5320p OVNH
		 5320c Magic Time High = at 50% LowerNHOD Buy Call, Exit Same High
		 5320c 10% = Buy Call
"""
