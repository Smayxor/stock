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
	
	straddles = [dp.calcZeroGEX( strikes )]  #****** EGEX conveersion
	callEGEX = [(x[dp.GEX_STRIKE], x[dp.GEX_CALL_OI] * x[dp.GEX_CALL_VOLUME]) for x in strikes]
	putEGEX = [(x[dp.GEX_STRIKE], x[dp.GEX_PUT_OI] * x[dp.GEX_PUT_VOLUME]) for x in strikes]
	mostCallEGEX = max(callEGEX, key=lambda i: i[1])[1] * 0.5
	mostPutEGEX = max(putEGEX, key=lambda i: i[1])[1] *0.5
	callWalls = [x[0] for x in callEGEX if x[1] > mostCallEGEX]
	putWalls = [x[0] for x in putEGEX if x[1] > mostPutEGEX]
	return (priceBounds, DAY_RANGE, straddles, putWalls, callWalls)
	
	lastPutVolume = 0
	for x in reversed(strikes):  #Detect PVN Nodes
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

def getStrike( strike, strikes ): return next((x for x in strikes if x[dp.GEX_STRIKE] == strike), None)

class Signal:	
	def __init__(self, firstTime, strikes, deadprice, ema1, ema2):
		self.deadprice = deadprice
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
		self.LargestCandle = 0
		self.isPreMarket = True
		self.callTimes = [] # [[strike, time],[next, -1]]
		self.putTimes = []
		self.ExtraDisplayText = ""
		self.EMA_PERIOD_1 = ema1 if ema1 > 2 else None
		self.EMA_PERIOD_2 = ema2 if ema2 > 2 else None
		self.SMAs1 = None
		self.EMAs1 = None
		self.SMAs2 = None
		self.EMAs2 = None
		self.totalCallVolume = []
		self.totalPutVolume = []
		self.VolumeDelta = []
		self.Signals = [SignalEMA(self, strikes), SignalDeadPrices(self, strikes, price) ]
		#self.Signals = [SignalDeadPrices(self, strikes, price) ]
		#self.Signals = [SignalEMA(self, strikes)]

	def getVolumeDeltaLen(self): return len(self.VolumeDelta) #len(self.totalCallVolume)
	def getVolumeDelta(self, index):
		#return (self.totalCallVolume[index] - self.totalCallVolume[index-30]) - (self.totalPutVolume[index] - self.totalPutVolume[index-30]) if index > 29 else 0
		if index < 30 : return 0
		return self.VolumeDelta[index] - self.VolumeDelta[index-30]

	def addTime(self, minute, strikes):
		price = dp.getPrice("SPX", strikes)
		self.Prices.append(price)
		self.PrevDataTimes.append( minute )
		self.PrevData[minute] = strikes	
		lastPriceIndex = len(self.Prices)-1
		
		
		allCallVol = sum( [x[dp.GEX_CALL_VOLUME] for x in strikes] )
		allPutVol = sum( [x[dp.GEX_PUT_VOLUME] for x in strikes] )
		#self.totalCallVolume.append( allCallVol )
		#self.totalPutVolume.append( allPutVol )
		self.VolumeDelta.append( allCallVol - allPutVol )

		if minute < 631 : 
			if price < self.OVNL : self.OVNL = price
			if price > self.OVNH : self.OVNH = price
			
			if len(self.Prices) > 1:
				wick = abs(self.Prices[lastPriceIndex] - self.Prices[lastPriceIndex-1])
				if wick > self.LargestCandle : self.LargestCandle = wick
			for siggy in self.Signals :
				result = siggy.addTime(minute, strikes, price)
		
		elif self.isPreMarket:# Fill list of contracts with OVNL and OVNH data
			self.isPreMarket = False
			self.OpenPrice = price
			self.Low = price
			self.High = price
		
		if self.EMAs1 == None and self.EMA_PERIOD_1 != None and lastPriceIndex > self.EMA_PERIOD_1 :
	
			self.SMAs1 = calcSMA( self.Prices, self.EMA_PERIOD_1 )
			self.EMAs1 = calcEMA( self.SMAs1, self.EMA_PERIOD_1 )
		
			if self.EMAs2 == None and self.EMA_PERIOD_2 != None and lastPriceIndex > self.EMA_PERIOD_2 :
				self.SMAs2 = calcSMA( self.Prices, self.EMA_PERIOD_2 )
				self.EMAs2 = calcEMA( self.SMAs2, self.EMA_PERIOD_2 )

		else :
			
			if self.EMAs1 != None and self.EMA_PERIOD_1 != None :
				self.SMAs1.append( appendSMA( self.Prices, self.EMA_PERIOD_1 ) )
				self.EMAs1.append( appendEMA( self.SMAs1, self.EMAs1, self.EMA_PERIOD_1 ) )
		
			if self.EMAs2 != None and self.EMA_PERIOD_2 != None :
				self.SMAs2.append( appendSMA( self.Prices, self.EMA_PERIOD_2 ) )
				self.EMAs2.append( appendEMA( self.SMAs2, self.EMAs2, self.EMA_PERIOD_2 ) )
			
		if price < self.Low : self.Low = price
		if price > self.High : self.High = price
		
		result = 0
		for siggy in self.Signals :
			result = siggy.addTime(minute, strikes, price)
			break
		
		return result
		
class SignalDeadPrices():	
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		self.PrevDataTimes = []
		self.PrevData = {}
		self.Owner.callTimes = [[x[dp.GEX_STRIKE], -1, x[dp.GEX_CALL_BID], x[dp.GEX_CALL_BID]] for x in strikes if (x[dp.GEX_CALL_BID] > self.Owner.deadprice) and (x[dp.GEX_STRIKE] % 5 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		self.Owner.putTimes = [[x[dp.GEX_STRIKE], -1, x[dp.GEX_PUT_BID], x[dp.GEX_PUT_BID]] for x in strikes if (x[dp.GEX_PUT_BID] > self.Owner.deadprice) and (x[dp.GEX_STRIKE] % 5 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		self.LargestCandle = 0
		wholePrice = int(price)

	def testContract( self, o, cp, lastPriceIndex, strikes, price ):
		bid = next((x[cp] for x in strikes if x[dp.GEX_STRIKE] == o[0]), None)
		if bid == None : 
			o[1] == -2
			return
		if bid > o[3] : o[3] = bid
		if bid <= o[3] * self.Owner.deadprice :
			txt = f'{"{:.0%}".format(bid / o[3])} - {o[0]}'
			o[1] = lastPriceIndex if abs(price - o[0]) < 3 else -2  #Only show flags when SPX Spot Price is near Strike Price
			o[0] = txt
				
	def addTime(self, minute, strikes, price):
		#self.PrevDataTimes.append( minute )
		#self.PrevData[minute] = strikes	
		lastPriceIndex = len(self.Owner.Prices)-1
		
		if self.Owner.isPreMarket: # Fill list of contracts with OVNL and OVNH data
			pass
		else : pass
		for c in [c for c in self.Owner.callTimes if c[1] == -1] : self.testContract( c, dp.GEX_CALL_BID, lastPriceIndex, strikes, price )
		for p in [p for p in self.Owner.putTimes if p[1] == -1] : self.testContract( p, dp.GEX_PUT_BID, lastPriceIndex, strikes, price )

		return 0
		
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

class Signal2x50():
	def __init__(self, owner, firstTime, strikes, deadprice):
		self.Owner = owner
		self.pickNodes(strikes)
		self.FindNodes = True

	def pickNodes(self, strikes):
		self.FindNodes = False
		strike = next(x for x in strikes if x[dp.GEX_STRIKE] == self.Upper50)
		self.callTimes = [[self.Upper50, 0, strike[dp.GEX_CALL_BID], strike[dp.GEX_CALL_BID]]]
		strike = next(x for x in strikes if x[dp.GEX_STRIKE] == self.Lower50)
		self.putTimes = [ [self.Lower50, 0, strike[dp.GEX_PUT_BID], strike[dp.GEX_PUT_BID]]]
		
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

FIBS = [0.786, 0.618, 0.5, 0.33, 0.236, -1]
#FIBS = [-1, -0.786, -0.618, -0.5, -0.382, -0.236, 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
AS_STRIKE, AS_CALL_BID, AS_CALL_LOW, AS_CALL_HIGH, AS_PUT_BID, AS_PUT_LOW, AS_PUT_HIGH = 0, 1, 2, 3, 4, 5, 6
class SignalPercentages(): #Blank Signal example
	def __init__(self, owner, strikes):
		self.Owner = owner
		self.Upper50 = 99999
		self.Lower50 = 0
		self.Targets = []
		self.SPXBottom = []
		self.LastFlag = 0
		self.LastSPXStrike = 0
		self.setAllStrikes( strikes )
		
	def setStrikeHigh(self, strikes):
		for strike in strikes :
			storedStrike = next((x for x in self.allStrikes if strike[dp.GEX_STRIKE] == x[AS_STRIKE]), None)
			if storedStrike == None : continue #print( strike[dp.GEX_STRIKE], ' not found')
			cBid = strike[dp.GEX_CALL_BID]
			pBid = strike[dp.GEX_PUT_BID]
			storedStrike[AS_CALL_BID] = cBid
			if cBid < storedStrike[AS_CALL_LOW] : storedStrike[AS_CALL_LOW] = cBid
			if cBid > storedStrike[AS_CALL_HIGH] : storedStrike[AS_CALL_HIGH] = cBid
			storedStrike[AS_PUT_BID] = pBid
			if pBid < storedStrike[AS_PUT_LOW] : storedStrike[AS_PUT_LOW] = pBid
			if pBid > storedStrike[AS_PUT_HIGH] : storedStrike[AS_PUT_HIGH] = pBid
	
	def setAllStrikes(self, strikes):
		self.allStrikes = [[x[dp.GEX_STRIKE], x[dp.GEX_CALL_BID], x[dp.GEX_CALL_BID], x[dp.GEX_CALL_BID], x[dp.GEX_PUT_BID], x[dp.GEX_PUT_BID], x[dp.GEX_PUT_BID]] for x in strikes]
	
	def addTime(self, minute, strikes, price):
		result = 0

		self.setStrikeHigh(strikes)
		if self.Owner.isPreMarket : return 0
		
		if len(self.Targets) < 2 : 
			mostOIVolCall = max(strikes, key=lambda i: i[dp.GEX_CALL_OI] + i[dp.GEX_CALL_VOLUME])
			mostOIVolPut  = max(strikes, key=lambda i: i[dp.GEX_PUT_OI] + i[dp.GEX_PUT_VOLUME])
			#self.Targets = [mostOIVolCall[dp.GEX_STRIKE], mostOIVolPut[dp.GEX_STRIKE]]
			d, m = divmod( price, 25 )
			d = 25 * (d + (m > 12.5))
			strk = ((price + 12.5) // 25) * 25 #Round to nearest 25 points
			self.Targets = [strk, strk]
			self.ExtraDisplayText = f'{self.Targets[0]} - {self.Targets[1]}'
		
		callStrike = next((x for x in self.allStrikes if x[AS_STRIKE] == self.Targets[0]), None)
		putStrike = next((x for x in self.allStrikes if x[AS_STRIKE] == self.Targets[1]), None)
		
		if  callStrike[AS_CALL_BID] <= callStrike[AS_CALL_HIGH] * 0.666 : 
			result = 1
			callStrike[AS_CALL_HIGH] = callStrike[AS_CALL_BID]
		if  callStrike[AS_PUT_BID] <= callStrike[AS_PUT_HIGH] * 0.666  : 
			result = -1
			callStrike[AS_PUT_HIGH] = callStrike[AS_PUT_BID]

		if minute < 630 : result = 0

		if self.LastFlag > 0 : self.LastFlag -= 1
		if result != 0 and self.LastFlag == 0 : self.LastFlag = 20
		else : result = 0

		return result

class SignalEMA:
	def __init__(self, owner, strikes):
		self.Owner = owner
		self.LastResult = 0
		self.MostEMADif = 0
		
	def addTime(self, minute, strikes, price):
		if self.Owner.isPreMarket: return 0
		if self.Owner.EMAs1 == None or self.Owner.EMAs2 == None : return 0
		result = 0
		
		#print(1)
		if minute < 710 :
		#	print(2)
			emaDif = abs(self.Owner.EMAs1[-1] - self.Owner.EMAs2[-1])
			emaOver = self.Owner.EMAs1[-1] > self.Owner.EMAs2[-1]
			if emaOver == False : emaOver = -1
			
			if emaDif > self.MostEMADif : self.MostEMADif = emaDif
			if self.MostEMADif - emaDif > 1 : result = 1 * emaOver
			if emaDif < 1 :	
				self.MostEMADif = 0
				self.LastResult = 0
				result = 0
			if self.LastResult != result and result != 0 : self.LastResult = result
			else : result = 0
		#	print(3)
		else:
		#	print(4)
			emaOver = self.Owner.EMAs1[-1] > self.Owner.EMAs2[-1]
			#topEMA = self.Owner.EMAs1 if emaOver else self.Owner.EMAs2
			#bottomEMA = self.Owner.EMAs2 if emaOver else self.Owner.EMAs1
			
			def calcTopAngle( emas ):
				result = 0 #nonlocal result
				tmp = emas[-20:]
				
				peak = max( tmp )
				valley = min( tmp )
				
				p2v = peak - valley
				p2e = peak - tmp[19]
				e2v = tmp[19] - valley
				if p2v > 1.5 and p2e > 1.5 : result = 1
				if p2v > 1.5 and e2v > 1.5 : result = -1
				return result
			
			#result = calcTopAngle( self.Owner.EMAs2 )
			
			#if 743 < minute < 752 :
			#	if self.LastResult != 3 : print('start')
			#	self.LastResult = 3
			#	print( self.Owner.EMAs2[-1] )
				
			#print(5)
		#print(6)
		return result

"""
5292.667821026301
5292.591853566973
5292.494243827524
5292.336199495247
5292.1341632233825
5291.9079517282225
5291.6483241412725
5291.375901570132
5291.06482855738
5290.778496092401
5290.526951348327
5290.325687466813
5290.194653381937
5290.1501709488575
5290.159230776338
5290.212097907912
5290.3189891973825
5290.478263888767
5290.731306818082
5291.011069214795
5291.302692993922
5291.593112449572
5291.875273822377
"""


def calcSMA(prices, period): 
	result = [(sum( prices[i-period:i] ) / period) for i in range( period, len(prices) +1 )]
	return result
	
def calcEMA(smas, period):	#EMA_THIS = a_0 * [2 / (n + 1)] + EMA_PREV * [1 - [2 / (n + 1)]]
	emas = [smas[0]]
	for i in range(1, len(smas) ):
		emas.append( (smas[i] * (2/(period+1))) + (emas[-1] * (1-(2/(period+1)))) )
	return emas

def appendSMA(prices, period): return sum(prices[-period:]) / period

def appendEMA(smas, emas, period): return (smas[-1] * (2/(period+1))) + (emas[-1] * (1-(2/(period+1))))

#prd = 5
#test = [0, 1, 1, 1, 5, 6, 7, 2, 3, 9, 9, 5, 6, 3, 5, 4, 3, 2, 1]
#print( test[-prd:] )
#print([test[i-prd:i] for i in range( prd, len(test) + 1 )] )

#strike = next((x for x in strikes if x[dp.GEX_STRIKE] == self.Upper50), None)
#https://studylib.net/doc/26075953/recognizing-over-50-candlestick-patterns-with-python-by-c
#EMA = Closing price * multiplier + EMA (previous day) * (1-multiplier). The multiplier is calculated using the formula 2 / (number of observations +1)
#EMA_1 = close_curr * [2 / (20 + 1)] + EMA_prev * [1 - [2 / (20 + 1)]]

#An increase in IV hints at Retail Buying = High IV is Handicapping
#Bounce at PutSupport = MarketMaker Long Gamma = Will be support
#Break at a Range Expansion = Those are long puts if we're going down
"""
Top S&P 500 index funds in 2024
Fund (ticker)	5-year annual returns	Expense ratio	Minimum investment
Source: Morningstar, as of April 4, 2024
Fidelity ZERO Large Cap Index (FNILX)	14.6%	0%	None
Vanguard S&P 500 ETF (VOO)	14.5%	0.03%	None
SPDR S&P 500 ETF Trust (SPY)	14.5%	0.095%	None
iShares Core S&P 500 ETF (IVV)	14.5%	0.03%	None
Schwab S&P 500 Index (SWPPX)	14.5%	0.02%	None
Vanguard 500 Index Fund (VFIAX)	14.5%	0.04%	$3,000
Fidelity 500 index fund (FXAIX)	14.5%	0.015%	None
"""
"""
Day 0 - Open 4900 - Nlargest 4900, 4875, 4925.   BestPlay 11:45  - No PVN or it is 4900?
		4875p High $13.90 -> 11:45 -> $2.05 - 14.7%
		4925c High $8.60 -> $1.20 - 13.9%
		4900p OVNL $8.60 -> $31.30 -> 11:45 -> $8.80 - 28%
		4900c OVNH $20.20 -> $3.90 - 19.3% -> $12.10 - 310%
		
Day 1 - Open 4866 - 4850, 4890   BestPlay 8:12  - No PVN
		4850c OVNH $26.90 -> $12.40 - 46% -> $54.90 - 442%
		4850p OVNH $8.20 -> 7:30 - $2.15 - 26% -> $9.40 - 437%
		
Day 2 - Open 4910 - 4900 - Volume>OI - 4950 - No PVN

Day 3 - Open 4945 - 4925, 4985, 4990.  Best Play 6:55 -> 7:45 -> 9:42.   Late PVN 4980, 4990
		4950c OVNH $13.10
		4925p HOD $13.20 -> Enter Call

Day 4 - Open 4950 - 4900, 4960, 4980.  Best Play 6:45.  PVN 4980

Day 5 - Open 4975 - 4950,  4930, 5000.  Best Play 7:04.    PVN 4990, 5000  Breach

Day 6 - Open 4995 - 5000.  Best Play NA.  PVN 5030, 5035

Day 7 - Open 5000 - 5000 5100. Best Play 6:50.  No PVN

Day 8 - Open 5025 - 5000 5050. Best Play 7:14.  PVN 5060, 5065, 5070

Day 9 - Open 4950 - 5050.  Best Play 9:45.  No PVN

Day 10 - Open 4980 - 4950 5000.  Best Play 7:26 -> 9:05 -> EOD.  No PVN


"""
