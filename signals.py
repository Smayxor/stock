#This module intended to identify trade signals
import datapuller as dp
import heapq

DAY_RANGE, DAY_PUMP, DAY_DUMP, DAY_CRAZY, DAY_CONDOR, DAY_BREACH = 0, 1, 2, 3, 4, 5

GEX_STRIKE, GEX_TOTAL_GEX, GEX_TOTAL_OI, GEX_CALL_GEX, GEX_CALL_OI, GEX_PUT_GEX, GEX_PUT_OI, GEX_CALL_IV, GEX_CALL_BID, GEX_CALL_ASK, GEX_PUT_BID, GEX_PUT_ASK, GEX_CALL_VOLUME, GEX_CALL_BID_SIZE, GEX_CALL_ASK_SIZE, GEX_PUT_VOLUME, GEX_PUT_BID_SIZE, GEX_PUT_ASK_SIZE, GEX_CALL_SYMBOL, GEX_PUT_SYMBOL, GEX_PUT_IV, GEX_CALL_DELTA, GEX_PUT_DELTA = dp.GEX_STRIKE, dp.GEX_TOTAL_GEX, dp.GEX_TOTAL_OI, dp.GEX_CALL_GEX, dp.GEX_CALL_OI, dp.GEX_PUT_GEX, dp.GEX_PUT_OI, dp.GEX_CALL_IV, dp.GEX_CALL_BID, dp.GEX_CALL_ASK, dp.GEX_PUT_BID, dp.GEX_PUT_ASK, dp.GEX_CALL_VOLUME, dp.GEX_CALL_BID_SIZE, dp.GEX_CALL_ASK_SIZE, dp.GEX_PUT_VOLUME, dp.GEX_PUT_BID_SIZE, dp.GEX_PUT_ASK_SIZE, dp.GEX_CALL_SYMBOL, dp.GEX_PUT_SYMBOL, dp.GEX_PUT_IV, dp.GEX_CALL_DELTA, dp.GEX_PUT_DELTA

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
	#callEGEX = [(x[dp.GEX_STRIKE], x[dp.GEX_CALL_OI] * x[dp.GEX_CALL_VOLUME]) for x in strikes]
	#putEGEX = [(x[dp.GEX_STRIKE], x[dp.GEX_PUT_OI] * x[dp.GEX_PUT_VOLUME]) for x in strikes]
	bothEGEX = [(x[dp.GEX_STRIKE], x[dp.GEX_CALL_OI] * x[dp.GEX_CALL_VOLUME], x[dp.GEX_PUT_OI] * x[dp.GEX_PUT_VOLUME]) for x in strikes]
	
	mostCallEGEX = max(bothEGEX, key=lambda i: i[1])[1] * 0.8
	mostPutEGEX = max(bothEGEX, key=lambda i: i[2])[2] *0.8
	
	callWalls = [x[0] for x in bothEGEX if x[1] > mostCallEGEX]
	putWalls = [x[0] for x in bothEGEX if x[2] > mostPutEGEX]
	
	mostCallEGEX *= 0.6
	mostPutEGEX *= 0.6
	straddles = straddles + [x[0] for x in bothEGEX if x[1] > mostCallEGEX and x[2] > mostPutEGEX]

	
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
		last = index + 50
		if last > lenavgs : return False
		for i in range(index, last):
			if prices[i] > prices[index] : return False
		return True
	def checkNextLow(index):
		#last = index + 30 if index + 30 < lenavgs else lenavgs
		last = index + 50
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

class OptionPosition : #Class used for backtesting
	BID_E = [dp.GEX_PUT_BID, dp.GEX_CALL_BID]  # Call is 1,  so Put is 0
	ASK_E = [dp.GEX_PUT_ASK, dp.GEX_CALL_ASK]
	def __init__(self, isCall, strike, entryPrice, SL=-1, TP=-1, isFilled=False):
		self.isCall = isCall == 1
		self.Strike = strike
		self.isFilled = isFilled
		self.isClosed = False
		self.EntryPrice = entryPrice
		self.SL = SL
		self.TP = TP
	def addTime(self, minute, strikes, price):
		strike = getStrike( self.Strike, strikes )
		pnlChange = 0
		if strike == None :
			print( f'Option {self.Strike} not found')
			return
		bid = strike[self.BID_E[self.isCall]]
		ask = strike[self.ASK_E[self.isCall]]
		if self.isFilled :
			if bid >= self.TP :
				self.TP += 0.5
				self.SL = self.TP - 0.4
			
				#self.isClosed = True
				#pnlChange = self.TP
				#print(f'{minute} - ******** WINNER ******* {"Call" if self.isCall else "Put"} at {self.TP}')
			if bid <= self.SL or minute > 1259 :
				self.isClosed = True
				pnlChange = bid
				print(f'{minute} - Stopped Out of {"Call" if self.isCall else "Put"} at {bid}')
		else : #not filled
			if ask <= self.EntryPrice :
				self.isFilled = True
				pnlChange = -self.EntryPrice
				print(f'{minute} - Filled {"Call" if self.isCall else "Put"} at {self.EntryPrice}')
		return pnlChange

class Signal:	
	def __init__(self, day, firstTime, strikes, deadprice, ema1, ema2):
		self.deadprice = deadprice
		price = dp.getPrice("SPX", strikes)
		self.OVNH = 0
		self.OVNL = 99999
		self.OpenPrice = -1
		self.Low = price
		self.High = price
		self.Prices = []
		self.PrevData = {}
		self.PrevDataTimes = []
		self.PrevData[firstTime] = strikes
		self.LargestCandle = 0
		self.isPreMarket = True
		self.callTimes = [] # [[strike, time],[next, -1]]
		self.putTimes = []
		self.ExtraDisplayText = ""
		self.EMA_PERIOD_1 = 2#ema1 if ema1 > 2 else None
		self.EMA_PERIOD_2 = 4#ema2 if ema2 > 2 else None
		self.SMAs1,self.EMAs1,self.SMAs2,self.EMAs2 = None,None,None,None
		
		self.totalCallVolume = []
		self.totalPutVolume = []
		self.VolumeDelta = []
		self.CallSpread = []
		self.PutSpread = []
		
		self.Yesterday = dp.fetchPreviousDaysLevels(day)
		
		#self.Signals = [SignalGEX(self, strikes, price), SignalEMA(self, strikes), SignalDeadPrices(self, strikes, price) ]
		self.Signals = [SignalOVD(self, strikes, price), SignalDeadPrices(self, strikes, price) ]
		#self.Signals = [SignalEMA(self, strikes)]
		#self.Signals = [SignalGEX(self, strikes, price)]
		
		#*****  Strike, LastPrice, Low, High
		self.CallPrices = [[x[dp.GEX_STRIKE], x[dp.GEX_CALL_BID], x[dp.GEX_CALL_BID], x[dp.GEX_CALL_ASK]] for x in strikes if 0.3 < x[dp.GEX_CALL_BID] < 20]
		self.PutPrices = [[x[dp.GEX_STRIKE], x[dp.GEX_PUT_BID], x[dp.GEX_PUT_BID], x[dp.GEX_PUT_ASK]] for x in strikes if 0.3 < x[dp.GEX_PUT_BID] < 20]

	def getOVD(self, index, cp=0):
		o = self.totalCallVolume if cp else self.totalPutVolume if cp == -1 else self.VolumeDelta
		if index == -1 : index = len(o) -1
		delta = 0 if index < 30 else o[index-30]
		return o[index] - delta
		
	def getCallSpreadDelta(self, index):
		if index < 30 : return 0
		return self.CallSpread[index]# - self.CallSpread[index-30]
		
	def getPutSpreadDelta(self, index):
		if index < 30 : return 0
		return self.PutSpread[index]# - self.PutSpread[index-30]

	def findContractWithPrice(self, strike, cp):
		# round(((n // 0.05) + 1) * 0.05, 2)
		isCall = cp == 'c'
		element = dp.GEX_CALL_BID if isCall else dp.GEX_PUT_BID
		bids = []
		symbol = None
		for minute, strikes in self.PrevData.items():
			strk = next((x for x in strikes if strike == x[dp.GEX_STRIKE]), None)
			if strk is None :
				print(f'Strike {strike} not found!')
				return None
			bids.append( strk[element] )
		symbol = strk[dp.GEX_CALL_SYMBOL if isCall else dp.GEX_PUT_SYMBOL]
		bids = [x for x in bids if x > 0]
		lastPrice = bids[-1]
		lowestPrice = min(bids)
		print(symbol, lowestPrice, lastPrice)
		return (symbol, lowestPrice, lastPrice)

	def updateLowHighPrices(self, strikes):
		def updateCons( cpPrices, element ):
			for cp in cpPrices :
				strike = next(x for x in strikes if x[dp.GEX_STRIKE] == cp[0])
				cp[1] = strike[element]
				if cp[1] < cp[2] : cp[2] = cp[1]
				if cp[1] > cp[3] : cp[3] = cp[1]
		updateCons( self.CallPrices, dp.GEX_CALL_ASK )
		updateCons( self.PutPrices, dp.GEX_PUT_ASK )

	def addTime(self, minute, strikes):
		price = dp.getPrice("SPX", strikes)
		self.Prices.append(price)
		self.PrevDataTimes.append( minute )
		self.PrevData[minute] = strikes	
		lastPriceIndex = len(self.Prices)-1
		self.updateLowHighPrices(strikes)
		
		allCallVol, allPutVol, allCallSpread, allPutSpread = 0, 0, 0, 0
		for x in strikes:
			allCallVol += x[dp.GEX_CALL_VOLUME]
			allPutVol += x[dp.GEX_PUT_VOLUME]
			
			allCallSpread += (x[dp.GEX_CALL_ASK] - x[dp.GEX_CALL_BID] - 0.05) / 0.05
			allPutSpread += (x[dp.GEX_PUT_ASK] - x[dp.GEX_PUT_BID] - 0.05) / 0.05
			
		self.totalCallVolume.append( allCallVol )
		self.totalPutVolume.append( allPutVol )
		self.VolumeDelta.append( allCallVol - allPutVol )
		
		#lenStrikes = len(strikes)
		#self.CallSpread.append( allCallSpread / lenStrikes )
		#self.PutSpread.append( allPutSpread / lenStrikes )

		if minute < 631 : 
			if price < self.OVNL : self.OVNL = price
			if price > self.OVNH : self.OVNH = price
			
			if len(self.Prices) > 1:
				wick = abs(self.Prices[lastPriceIndex] - self.Prices[lastPriceIndex-1])
				if wick > self.LargestCandle : self.LargestCandle = wick
			#for siggy in self.Signals :
			#	result = siggy.addTime(minute, strikes, price)
		elif self.isPreMarket:# Fill list of contracts with OVNL and OVNH data
			self.isPreMarket = False
			self.OpenPrice = price
			#self.Low = price
			#self.High = price
		
		if self.EMA_PERIOD_1 != None :
			if self.EMAs1 == None :
				if lastPriceIndex +1 == self.EMA_PERIOD_1 :
					self.SMAs1 = calcSMA( self.Prices, self.EMA_PERIOD_1 )
					self.EMAs1 = calcEMA( self.SMAs1, self.EMA_PERIOD_1 )
			else :
				self.SMAs1.append( appendSMA( self.Prices, self.EMA_PERIOD_1 ) )
				self.EMAs1.append( appendEMA( self.SMAs1, self.EMAs1, self.EMA_PERIOD_1 ) )
		if self.EMA_PERIOD_2 != None :
			if self.EMAs2 == None :
				if lastPriceIndex +1 == self.EMA_PERIOD_2 :
					self.SMAs2 = calcSMA( self.Prices, self.EMA_PERIOD_2 )
					self.EMAs2 = calcEMA( self.SMAs2, self.EMA_PERIOD_2 )
			else :
				self.SMAs2.append( appendSMA( self.Prices, self.EMA_PERIOD_2 ) )
				self.EMAs2.append( appendEMA( self.SMAs2, self.EMAs2, self.EMA_PERIOD_2 ) )
		
		if price < self.Low : self.Low = price
		if price > self.High : self.High = price
		
		result = 0
		msg = ""
		for siggy in self.Signals :
			signalResult = siggy.addTime(minute, strikes, price)
			if signalResult[0] != 0 : 
				msg = signalResult[1]
				result = signalResult[0]
		
		#if result != 0 : print( minute, msg )
				
		return (result, msg)

class SignalOVD():
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		self.AverageOVD = 0
		self.Surges = []
		
	def addTime(self, minute, strikes, price):
		vd = self.Owner.VolumeDelta
		lvd = len(vd)-1
		
		if lvd < 50: return (0, "")
		result = 0

		ovd = self.Owner.getOVD(lvd, 0)
		povd = self.Owner.getOVD(lvd - 5, 0)
		ovds = (ovd, povd)
		minOVD = min(ovds)
		maxOVD = max(ovds)
		difOVD = maxOVD - minOVD
		msg = ""
		if difOVD > 10000:
			result = 1 if ovd > 0 else - 1
			surge = (minute, result, vd[lvd], difOVD, minOVD, maxOVD)
			#print( surge )
			for s in self.Surges :
				if minute - s[0] < 10 : result = 0
			self.Surges.append( surge )	
			msg = "OVD Call Surge" if result == 1 else "OVD Put Surge"

		return (result, msg)

class SignalVolatility():
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		self.Stage = 0
		self.OpenStrike = None
		self.TargetCall = None
		self.TargetPut = None
		self.TargetCallHigh = 0
		self.TargetCallLow = 9999999
		self.TargetPutHigh = 0
		self.TargetPutLow = 99999999
		
		self.HOD = 0
		self.LOD = 99999999
		
		self.Zones = {}
		self.PriceZones = []

	def getHighLow(self, strike):
		pass

	def addTime(self, minute, strikes, price):
		lastPriceIndex = len(self.Owner.Prices)-1
		if minute < 631 : return 0
		if self.Stage == -1 : return 0
		result = 0

		if price > self.HOD : self.HOD = price
		if price < self.LOD : self.LOD = price

		priceZone = price // 25
		self.PriceZones.append( priceZone )
		self.Zones[priceZone] = self.Zones.get(priceZone, 0) + 1

		if self.Stage == 0 :
			strikeATM = sorted( strikes, key=lambda strike: abs(strike[dp.GEX_STRIKE] - price) )[0]
			isHighIV = (strikeATM[GEX_CALL_BID] + strikeATM[GEX_PUT_BID]) > 30
			self.OpenStrike = strikeATM[GEX_STRIKE]
			self.Stage = 1 if isHighIV else -1
			result = self.Stage
		elif self.Stage == 1 :
			if minute > 650 : self.Stage = 2
		elif self.Stage == 2 :
			lastFew = self.Owner.Prices[-10:]
			high = max( lastFew )
			low = min( lastFew )
			dif = high - low
			if abs(dif) > 20:
				#result = 1 if dif > 0 else -1
				self.Stage = 3
				
				mostCallVolumeStrike = max( [ x for x in strikes ], key=lambda i: i[GEX_CALL_VOLUME] )
				mostPutVolumeStrike = max( [ x for x in strikes ], key=lambda i: i[GEX_PUT_VOLUME] )
				
				self.TargetCall = mostCallVolumeStrike[GEX_STRIKE]
				self.TargetPut = mostPutVolumeStrike[GEX_STRIKE]
				
				val = next(x for x in strikes if x[GEX_STRIKE] == self.TargetCall)[GEX_CALL_BID]
				self.TargetCallHigh, self.TargetCallLow = val, val
					
				#print( self.TargetCall, self.TargetCallHigh, self.TargetCallLow )
					
				val = next(x for x in strikes if x[GEX_STRIKE] == self.TargetPut)[GEX_PUT_BID]
				self.TargetPutHigh, self.TargetPutLow = val, val

		elif self.Stage == 3:
			callBid = next(x for x in strikes if x[GEX_STRIKE] == self.TargetCall)[GEX_CALL_BID]
			if callBid > self.TargetCallHigh : self.TargetCallHigh = callBid
			if callBid < self.TargetCallLow : self.TargetCallLow = callBid

			putBid = next(x for x in strikes if x[GEX_STRIKE] == self.TargetPut)[GEX_PUT_BID]
			if putBid > self.TargetPutHigh : self.TargetPutHigh = putBid
			if putBid < self.TargetPutLow : self.TargetPutLow = putBid
			
			if callBid <= self.TargetCallHigh * 0.5 : 
				result = 1
				self.Stage = 4
				
		elif self.Stage == 4:
			callBid = next(x for x in strikes if x[GEX_STRIKE] == self.TargetCall)[GEX_CALL_BID]
			putBid = next(x for x in strikes if x[GEX_STRIKE] == self.TargetPut)[GEX_PUT_BID]
			
			if callBid > self.TargetCallHigh * 0.8 :
				result = -1
				self.Stage = 5

		elif self.Stage == -1 : #First identify doouble taps off quarter strikes
			self.Stage = -2
		elif self.Stage == -2:
			pass

		return result

class SignalEGEX():
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		self.PivotNodes = None
		self.LastPivotNode = 0
		self.LastSignalIndex = 0
		
	def assignPivotNodes(self, strikes):
		callPutEGEX = [ [ x[dp.GEX_STRIKE], 0, x[dp.GEX_CALL_OI] * x[dp.GEX_CALL_VOLUME], x[dp.GEX_PUT_OI] * x[dp.GEX_PUT_VOLUME] ] for x in strikes]
		for x in callPutEGEX : x[1] = x[2] + x[3]
		mostCallEGEX = max( callPutEGEX, key=lambda i: i[2] )[2]
		mostPutEGEX = max( callPutEGEX, key=lambda i: i[3] )[3]
		
		mostEGEX = max( callPutEGEX, key=lambda i: i[1] ) [1]
		
	
		majorEGEX = mostEGEX * 0.6
		
		sumCalls = sum( [x[2] for x in callPutEGEX] )
		sumPuts = sum( [x[3] for x in callPutEGEX] )
		
		levels = [x for x in callPutEGEX if x[1] > majorEGEX]
		print( [x[0] for x in levels] )
		self.PivotNodes = levels
		self.PivotNodes.sort()
		#print( levels )
		
	def addTime(self, minute, strikes, price):
		lastPriceIndex = len(self.Owner.Prices)-1

		result = 0
		if self.Owner.isPreMarket : return 0
		if minute < 631 : return 0
		
		if self.PivotNodes == None : self.assignPivotNodes( strikes )
		tmp = 9999999
		if tmp != self.LastSignalIndex :
			result = tmp
			self.LastSignalIndex = tmp
		
		return 0#result
			
class SignalGEX():
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		self.PivotNodes = None
		self.LastPivotNode = 0
		self.LastSignalIndex = 0
		#self.assignPivotNodes( strikes )
		#print( f'init Nodes {self.PivotNodes}')
		
	def assignPivotNodes(self, strikes):
		sigs = identifyKeyLevels( strikes )
		levels = sigs[2] + [x for x in sigs[3] if x not in sigs[2]]
		levels = levels + [x for x in sigs[4] if x not in levels]
		self.PivotNodes = levels # sigs[2] + sigs[3] + sigs[4]
		self.PivotNodes.sort()
	
	def addTime(self, minute, strikes, price):
		lastPriceIndex = len(self.Owner.Prices)-1

		result = 0
		if self.Owner.isPreMarket : return 0
		if minute < 631 : return 0
		
		if self.PivotNodes == None :
			self.assignPivotNodes( strikes )
			#print( f'init Nodes {self.PivotNodes}')

		for node in self.PivotNodes :
			if self.LastPivotNode != node and abs(price - node) < 5 and lastPriceIndex - self.LastSignalIndex > 30 :
#				vd = self.Owner.getVolumeDelta(lastPriceIndex)
#				if vd < 3000 : break
				self.LastPivotNode = node
				self.LastSignalIndex = lastPriceIndex
				
				topNode = max( self.PivotNodes )
				bottomNode = min ( self.PivotNodes )
				
				if node == topNode : 
					trend = -1
					#print( node, topNode, self.PivotNodes )
				elif node == bottomNode : 
					trend =1
					#print( node, bottomNode, self.PivotNodes )
				else :
					sumPrices = []
					if minute < 650 :
						sumPrices = (sum(self.Owner.Prices) / lastPriceIndex+1)
					else :
						sumPrices = (sum(self.Owner.Prices[-10:]) / 10)
					trend = sumPrices > node
					if trend == 0 : trend = -1
				
				result = trend

		#if result != 0 : self.PivotNodes.remove( self.LastPivotNode )

		return result
		
def get_match():
    analog_value = 5134.2948392
    return analog_value // 0.25 * 0.25		

class SignalDeadPrices():	
	def __init__(self, owner, strikes, price):
		self.Owner = owner
		#, self.Owner.deadprice
		self.Owner.callTimes = [[x[dp.GEX_STRIKE], -1, x[dp.GEX_CALL_BID], x[dp.GEX_CALL_BID], self.Owner.deadprice] for x in strikes if (x[dp.GEX_CALL_BID] > self.Owner.deadprice) and (x[dp.GEX_STRIKE] % 25 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		self.Owner.putTimes = [[x[dp.GEX_STRIKE], -1, x[dp.GEX_PUT_BID], x[dp.GEX_PUT_BID], self.Owner.deadprice] for x in strikes if (x[dp.GEX_PUT_BID] > self.Owner.deadprice) and (x[dp.GEX_STRIKE] % 25 == 0) and (abs(x[dp.GEX_STRIKE] - price) < 100)]
		self.LargestCandle = 0
		self.LastFlag = -1
		wholePrice = int(price)

	def testContract( self, o, cp, lastPriceIndex, strikes, price ):
		bid = next((x[cp] for x in strikes if x[dp.GEX_STRIKE] == o[0]), None)
		result = 0
		if bid == None : 
			o[1] == -2
			return result
			
		if o[1] == -1 :
			if bid <= self.Owner.deadprice :
				o[1] = lastPriceIndex
				self.LastFlag = lastPriceIndex
				result = 1
				o[4] = bid
		elif o[1] > 0:
			if bid > o[4] : o[4] = bid
		return result
				
	def addTime(self, minute, strikes, price):
		lastPriceIndex = len(self.Owner.Prices)-1
		
		if self.Owner.isPreMarket: # Fill list of contracts with OVNL and OVNH data
			pass
		else : pass
		
		result = 0
		msg = ""
		
		for c in [c for c in self.Owner.callTimes if c[1] > -2] : 
			conres = self.testContract( c, dp.GEX_CALL_BID, lastPriceIndex, strikes, price )
			if conres == 1 : msg = f'{c[0]}c '
			result += conres
		for p in [p for p in self.Owner.putTimes if p[1] > -2] : 
			conres = self.testContract( p, dp.GEX_PUT_BID, lastPriceIndex, strikes, price )
			if conres == 1 : msg = f'{p[0]}p '
			result += conres
		
		if result != 0 and lastPriceIndex - self.LastFlag < 5 : 
			result = 0
			priceMod = (price % 25)
			if priceMod > 12.5 : priceMod = 25 - priceMod
			if priceMod < 5 : 
				self.LastFlag = -1
				#print( minute, price, priceMod )
				priceSlice = self.Owner.Prices[-10:]
				unders = 0
				for p in priceSlice :
					if price > p : unders += 1
					
				result = -1 if unders > 5 else 1
		else : result = 0
		
		return (result, msg)
		


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
		#if self.Owner.isPreMarket: return 0
		if self.Owner.EMAs1 == None or self.Owner.EMAs2 == None : return 0
		result = 0
		
		if minute < 710 :
			emaDif = abs(self.Owner.EMAs1[-1] - self.Owner.EMAs2[-1])
			emaOver = self.Owner.EMAs1[-1] < self.Owner.EMAs2[-1]
			if emaOver == False : emaOver = -1
			
			if emaDif > self.MostEMADif : self.MostEMADif = emaDif
			if self.MostEMADif - emaDif > 1 : result = 1 * emaOver
			if emaDif < 1 :	
				self.MostEMADif = 0
				self.LastResult = 0
				result = 0
			if self.LastResult != result and result != 0 : self.LastResult = result
			else : result = 0
		else:
			emaOver = self.Owner.EMAs1[-1] > self.Owner.EMAs2[-1]
			
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
			
		return result

#points = [5292.667821026301,5292.591853566973,5292.494243827524,5292.336199495247,5292.1341632233825,5291.9079517282225,5291.6483241412725,5291.375901570132,5291.06482855738,5290.778496092401,5290.526951348327,5290.325687466813,5290.194653381937,5290.1501709488575,5290.159230776338,5290.212097907912,5290.3189891973825,5290.478263888767,5290.731306818082,5291.011069214795,5291.302692993922,5291.593112449572,5291.875273822377]

def calcSMA(prices, period): 
#	result = [(sum( prices[i-period:i] ) / period) for i in range( period, len(prices) +1 )]
	summy = sum( prices ) / len( prices )
	result = [summy for x in range(period)]
	return result

#test = [1,1,1,1,1,1,1,1,1,2,3,4,5,6,7,8,9]
#print( calcSMA( test, 9 ) )

def calcEMA(smas, period):	#EMA_THIS = a_0 * [2 / (n + 1)] + EMA_PREV * [1 - [2 / (n + 1)]]
	return [smas[0] for x in range(period)]
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
=cbackpack sell --rarity normal rare epic legendary ascended —luck <50
=cbackpack disassemble --rarity ascended —lvl <200
=cbackpack disassemble --rarity ascended —level <200
=backpack trade 758033219177283696 1000 

Expected Value = avg_gain^(% of winning trades * # of all trades) - avg_loss^(% of losing trades * # of all trades)

Positive Delta = Makes money from price going up
Negative Delta = Makes money from price going down

Buy Put = Negative Delta
Short Put = Positive Delta  = Negative Gamma
Short Call = Negative Delta = Negative Gamma

Gamma is greatest ATM = Gamma Flip

When dealers are Short Gamma = Market Volatility = Dealer sells in to dips creating waterfalls in PA
When dealers are Long Gamma = Market Volatility Compression = Dealer buys the dips, and sells the rips

Traders are Long Puts and Short Calls

"""
