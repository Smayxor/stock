#This module intended to identify trade signals
import datapuller as dp
import heapq

DAY_RANGE, DAY_PUMP, DAY_DUMP, DAY_CRAZY, DAY_CONDOR, DAY_BREACH = 0, 1, 2, 3, 4, 5

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
	
class SignalDPT:
	def __init__(self, sigs, firstTime, firstStrike, deadprice):
		self.Lower50 = sigs[0][0]
		self.Upper50 = sigs[0][1]
		self.DayType = sigs[1]
		self.Straddles = sigs[2]
		self.PutWalls = sigs[3]
		self.CallWalls = sigs[4]
		self.AllNodes = sigs[2] + sigs[3] + sigs[4]
		self.deadprice = deadprice
		
		price = dp.getPrice("SPX", firstStrike)
		self.OVNH = price
		self.OVNL = price
		self.Prices = []
		self.PrevData = {}
		self.PrevData[firstTime] = firstStrike
		#********************** Variables for Peak and Valley
		self.Highs = []
		self.Lows = []
		self.HighIndex = 0
		self.LowIndex = 0
		self.lastOptionIndex = 0
		self.lastModulusIndex = 0
		self.bullFlag = 0
		#*********************
		
		self.callTimes = [[x[dp.GEX_STRIKE], -1] for x in firstStrike if (x[dp.GEX_CALL_BID] > deadprice) and (x[dp.GEX_STRIKE] % 25 == 0)]
		self.putTimes = [[x[dp.GEX_STRIKE], -1] for x in firstStrike if (x[dp.GEX_PUT_BID] > deadprice) and (x[dp.GEX_STRIKE] % 25 == 0)]
	#************************ Is it needed?
	def findPivots(self, price):
		if len(self.Prices) == 30 :
			for i in range( self.Prices ):
				thisPrice = self.Prices[i]
				if thisPrice > self.Prices[self.HighIndex] : self.HighIndex = i
				if thisPrice < self.Prices[self.LowIndex] : self.LowIndex = i
			self.Highs.append(self.HighIndex)
			self.Lows.append(self.LowIndex)
		else :
			thisIndex = len(self.Prices) - 1
			thisPrice = self.Prices[thisIndex]
			
			lastHigh = self.Prices[self.HighIndex]
			lastLow = self.Prices[self.LowIndex] 
			
			lastPivotIndex = max( (self.HighIndex, self.LowIndex) )
			lastPivot = self.Prices[lastPivotIndex] 
			
			if thisPrice > lastHigh : self.HighIndex = lastIndex
	#*****************************

	def addTime(self, minute, strikes):
		price = dp.getPrice("SPX", strikes)
		self.Prices.append(price)
		self.PrevData[minute] = strikes
		x = len(self.Prices) - 1
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
	
		result = (self.lastOptionIndex == x and x - self.lastModulusIndex < 5)
		return self.bullFlag if result else 0
		#if minute < 630 :
		#	if price > self.OVNH : self.OVNH = price
		#	if price < self.OVNL : self.OVNL = price
		#else :
		#	pass

	
	
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
	
	
"""
Day 0 - CrazyGEX - Puts From ONL   - Long Straddle						                     DPT - 4900 Breach - Target 4850p
Day 1 - CrazyGEX - Call and Puts from ONL.  Puts to ONH - Long Straddle                      DPT - 4850 Tap - Target 4900c
Day 2 - CrossedGEX - Calls win - Long Straddle  											 DPT - 4905* Tap - Target 4950c @ $1.50
Day 3 - CondorGEX - Puts win - Long Straddle												 DPT - 4950 Tap - Target 4900p
Day 4 - NormalGEX - Fomo Call.  Puts ONL.  													 DPT - 4950 Breach - Target 4900p
Day 5 - MinorStraddles - Fomo Call  - Long Straddle*									     DPT - OVN 4950 - Target 5000c @ $0.35
Day 6 - NISP Gex - Scalps only																 DPT - Ugly
Day 7 - DISP - HOD * 0.12 Call - Long Straddle												 DPT - 5000 Tap - Target 5050c
Day 8 - NISP - Fomo Call.   Puts HOD * 0.10 - Long Straddle									 DPT - Faulty Range
Day 9 - Dump - Call Scalp.   Puts HOD * 0.10.   Calls LOD $0.50 - Long Straddle				 DPT - 4945 Tap - Target 5005c ***
Day 10 - NormalGEX -  Calls ONL.  Puts ONL  - Long Straddle									 DPT - 4955 Tap - Target 5000c ***
Day 11 - CondorGEX - Puts ONL.  Calls ONL  - Long Straddle									 DPT - 5000 Tap - Target 5040c ***
Day 12 - Solo Straddle - Fomo Puts.  MAGIC TIME Calls.   Calls HOD * 0.10 - Long Straddle    Delete Day - Bad Data
Day 13 - NISP - Puts ONL - Long Straddle													 DPT - No Tap
Day 14 - Dump Day ISP - 4950 needs flagged.   Puts ONH * 0.10.  							 DPT - PowerHour 4950 Tap Target 4960c
Day 15 - Pump Day - Calls ONL.  															 DPT - DATA FAULT - 5050 Tap - Target 5100c
Day 16 - Pump Day - MAGIC TIME Puts.  														 DPT - Meh
Day 17 - NormalGEX or ISP? - Split PVN - Puts ONL											 DPT - No Tap - Target 5050p
Day 18 - NormalGEX - Puts ONL  																 DPT - No Tap
Day 19 - NISP - Calls ONL.  Puts HOD * 0.10 												 DPT - No Tap - Target 5050p
Day 20 - NormalGEX - Puts ONL.  Puts HOD * 0.10.  Calls HOD * 0.10.  Calls ONL				 DPT - Near Tap - Target @ $0.60 or $0.50
Day 21 - ISP GEX - 5100 Straddle Breach - Galactica - DPT Fail
Day 22 - ISP or Normalish GEX - No Tap - 5150c Needs Call Wall Flag!!!*!*!**!*!*!**!
Day 23 - NISP - Large 5140 should flag as Call Wall - DPT - Out of sync !*!*!*!*!**!*!*!**!
Day 24 - NISP - DPT - Out of sync
Day 25 - Normal GEX - DPT - Failure
Day 26 - Normal GEX  - DPT Tap ??5190?? Target 5125p
Day 27 - Data Fault - 2024-03-11  delete     DPT - 5100 Breach - Target 5150c
Day 28 - ISP GEX -  DPT Happened BEFORE OPEN
Day 29 - Normal GEX - DPT ???
Day 30 - FAKE PUMP DAY - DPT - 5150 Breach Target 5200c
Day 31 - ISP GEX - Negative Galactica - 5140p should flag as Call Wall - DPT ????
Day 32 - ??? GEX
Day 33 - Condor ISP GEX - DPT No
Day 34 - Normal GEX - Faulty Data
Day 35 - Crazy GEX - DPT - No
Day 36 - Fake Pump Day - DPT - No Tap
Day 37 - Normal Gex - No signals
Day 38 - Normal Gex - No signals
Day 39 - Normal Gex - Crab until -> DPT Target is HOD 5235 @$0.15 during PowerHour
Day 40 - Crazy GEX - DPT - No Tap
Day 41 - Missing signals?
Day 42 - Wide-Swath Normal GEX - DPT Fail
Day 43 - Normal GEX - DPT Trigger OVN  - Need ABS-GEX Trigger Level
Day 44 - Normal GEX - DPT Tap 5250 Target 5200p
Day 45 - Needs to trigger Breach Day - DPT Tap 5150 Target 5250c
Day 46 - Condor Day - DPT yes
Day 47 - Normal GEX - DPT Offset 25 points - Targets 5150p and 5200c
Day 48 - Normal GEX - DPT Offset Taps - Targets 5250c 5200c
Day 49 - Crazy GEX - DPT Fail
Day 50 - Normal GEX - DPT Fail
Day 51 - Normal GEX - DPT Fail
Day 52 - Condor GEX - DPT Mixed Results
Day 53 - Normal GEX - DPT ?Needs tuning?
Day 54 - Normal GEX - DPT Targets @ $0.25
Day 55 - Crazy GEX - DPT Fail
Day 56 - Normal GEX - DPT Target Put Support 
Day 57 - Normal GEX - DPT Targets %25 @ $0.40
Day 58 - Needs flagged as Condor Day - Condor Breach!!!
Day 59 - Normal GEX - DPT Tap 5000 Target 5050c @ $0.60   - 60 point OVN Drop
Day 60 - Normal GEX - DPT meh
Day 61 - Normal GEX - DPT 25-points @ 75 away
Day 62 - Normal GEX - DPT No Signals - Put Juiced
Day 63 - FOMC - DPT sort of
Day 64 - Normal Gex - DPT Fail
Day 65 - Normal GEX - Large OVN Pump 55 points - DPT Needs target adjustment to 0.55
"""