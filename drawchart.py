from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont
import PIL.Image as PILImg
import datapuller as dp

FONT_SIZE = 22
STR_FONT_SIZE = str(int(FONT_SIZE / 2))  #strangely font size is 2x on tkinter canvas
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic") #Place font file in same folder, or use supply path if needed in Linux
#ascent, descent = font.getmetrics()
#text_width = font.getmask(strike).getbbox()[2]
#text_height = font.getmask(text_string).getbbox()[3] + descent
IMG_W = 1000
IMG_H = 500

tmp = ['4', '5', '5', '6', '6', '7', '7', '7', '8', '8', '8', '9', '9', '9', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D', 'E', 'E', 'E', 'E', 'E', 'F', 'F', 'F', 'F', 'F', 'F', 'F']
tmp2 = ['f', 'e', 'e', 'e', 'c', 'c', 'c', 'b', 'b', 'a', 'a', '8', '8', '7', '7', '5', '5', '5', '4', '4', '4', '4', '3', '3', '3', '3', '2', '2', '2', '2', '1', '1', '1', '1', '1', '0', '0', '0', '0', '0', '0', '0']
LETTER = [ f'#{l}00' for l in reversed(tmp)] + ['#000'] + [ f'#0{l}0' for l in tmp]
TEXT_COLOR = [ f'#{l}{l}{l}' for l in reversed(tmp2)] + ['#FFF'] + [ f'#{l}{l}{l}' for l in tmp2]
MIDDLE_LETTER = len(tmp)
del tmp
def getColorGradient(maxVal, val):	return LETTER[int((val / maxVal) * MIDDLE_LETTER) + MIDDLE_LETTER]
def getTextColorGradient(maxVal, val):	return TEXT_COLOR[int((val / maxVal) * MIDDLE_LETTER) + MIDDLE_LETTER]

def drawRect(draw, x, y, w, h, color, border):
	if border in 'none': border = color
	try:	draw.rectangle([x,y,w,h], fill=color, outline=border)   #for PIL Image
	except:
		if x > w: drawRect( draw, w, y, x, h, color, border )
		elif y > h: drawRect( draw, x, h, w, y, color, border )
	
def drawPriceLine(draw, x, color):  #Draws a dashed line
	y = 100
	while y < 350:
		draw.line([x, y, x, y + 4], fill=color, width=1)
		y += 6

def drawRotatedPriceLine(draw, y, color):  #Draws a dashed line
	x = 120
	while x < 350:
		draw.line([x, y, x + 4, y], fill=color, width=1)
		x += 6

def drawText(draw, x, y, txt, color):
	draw.text((x,y), text=txt, fill=color, font=font)

def drawRotatedText(img, x, y, txt, color):
	text_layer = PILImg.new('L', (120, FONT_SIZE))
	dtxt = ImageDraw.Draw(text_layer)
	dtxt.text( (0, 0), txt, fill=255, font=font)
	rotated_text_layer = text_layer.rotate(270.0, expand=1)
	PILImg.Image.paste( img, rotated_text_layer, (x,y) )

#function recieves a Tuple Array from datapuller.py
def drawGEXChart(ticker, count, dte, chartType = 0, strikes = None, expDate = 0):
	ticker = ticker.upper()
	
	if strikes == None:
		optionsChains = dp.getOptionsChain(ticker, dte)
		expDate = optionsChains[0]
		strikes = dp.getGEX(optionsChains[1], chartType=chartType)
	
	atr = dp.getATR(ticker)
	atrs = atr[1]
	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	
	strikeLen = len( strikes[0] )
	for strike in strikes:
		for i in range(strikeLen):
			if strike[i] == None : print( strike )

	callDollars = sum([strike[4] * strike[9] for strike in strikes])  # Calc BEFORE shrinking count!!!
	putDollars = sum([strike[6] * strike[11] for strike in strikes])
	totalCalls = sum([strike[4] for strike in strikes]) 
	totalPuts = sum([strike[6] for strike in strikes]) 

	price = dp.getQuote(ticker)
	strikes = dp.shrinkToCount(strikes, price, count)
	count = len(strikes)
	#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk
	
	maxTotalGEX = max(strikes, key=lambda i: i[1])[1]
	minTotalGEX = abs(min(strikes, key=lambda i: i[1])[1])
	maxTotalGEX = max( (maxTotalGEX, minTotalGEX) )
	
	maxTotalOI = max(strikes, key=lambda i: i[2])[2]
	maxCallGEX = max(strikes, key=lambda i: i[3])[3]
	maxPutGEX = abs(min(strikes, key=lambda i: i[5])[5])
	maxCallPutGEX = max( (maxCallGEX, maxPutGEX) )
 
	"""	largeOI = maxTop * 0.77
		largeGEX = maxAbove * 0.87
		largeCall = maxUpper * 0.8
		largePut = maxLower * 0.8
		for i in sorted(strikes.Strikes) :
			if (top[i] > largeOI) or (above[i] > largeGEX) or (upper[i] > largeCall) or (lower[i] > largePut): keyLevels.append(i)
		keyLevels.append(zero)
		keyLevels.append(maxPain)
	"""
	#[(4265.0, 4265.405714285714), (4275.0, 4276.613811428571), (4285.0, 4285.412691428571), (4290.0, 4291.592857142857), (4300.0, 4297.773022857143), (4305.0, 4305.419668571429), (4320.0, 4317.78), (4330.0, 4330.140331428571), (4340.0, 4337.786977142857), (4345.0, 4343.967142857143), (4350.0, 4350.147308571429), (4360.0, 4358.946188571428), (4370.0, 4370.154285714286)]
	for i in range(len(atrs)):  #Should be done in the getATR code
		closestStrike = 0
		distToClosest = 99999
		for s in strikes:
			tmpDist = abs(atrs[i][1] - s[0])
			if distToClosest > tmpDist:
				distToClosest = tmpDist
				closestStrike = s[0]
		atrs[i] = (closestStrike, atrs[i][1])

	IMG_W = ((FONT_SIZE - 3) * count)   #IMG_W and IMG_H used backwards
	IMG_H = 500
	IMG_W += 110
	img = PILImg.new("RGB", (IMG_H, IMG_W), "#000")
	draw = ImageDraw.Draw(img)
	
	x = IMG_W - 15
	for strike in strikes :
		x -= FONT_SIZE - 3
		strikeColor = "#CCC"
		if strike[0] == maxPain : strikeColor = "#F00"
		if strike[0] == zeroG : strikeColor = "orange"
		strikeText = str(round((strike[0]), 2))		
		for i in range(len(atrs)):
			if atrs[i][0] == strike[0]: 
				strikeText = str(round(atrs[i][1], 1))	
		#strikeText = str(f'{round((abs(strike[8] - strike[10])), 2)}')		 #Call side has 2/3 value of Puts!!!  Could be used to determine SPX Price
		#strikeText = str(f'{round((strike[8]), 2)} - {round((strike[10]), 2)}')		
		drawText(draw, y=x - 5, x=218, txt=strikeText, color=strikeColor)
		
		if strike[2] != 0 : drawRect(draw, 0, x, ((strike[2] / maxTotalOI) * 65), x + 12, color="#00F", border='')
		if strike[1] != 0 : drawRect(draw, 215 - ((abs(strike[1]) / maxTotalGEX) * 150), x, 215, x + 12, color=("#0f0" if (strike[1] > -1) else "#f00"), border='')
		if (strike[3] != 0) : drawRect(draw, 399 - ((strike[3] / maxCallPutGEX) * 100), x, 399, x + 12, color="#0f0", border='')
		if (strike[5] != 0) : drawRect(draw, 401, x, 401 - ((strike[5] / maxCallPutGEX) * 100), x + 12, color="#f00", border='')
		
	x = 0
	drawText(draw, x=x, y=0, txt=f'{ticker} ' + "${:,.2f}".format(price, 2), color="#3FF")
	drawText(draw, x=x, y=FONT_SIZE * 1, txt="Calls "+"${:,.2f}".format(callDollars), color="#0f0")
	drawText(draw, x=x, y=FONT_SIZE * 2, txt="Puts "+"${:,.2f}".format(putDollars), color="#f00")
	drawText(draw, x=x, y=FONT_SIZE * 3, txt="Total "+"${:,.2f}".format(callDollars-putDollars), color="yellow")
	y = 0
	x = 260
	if chartType == 1: txt = f'Volume Exp {expDate}' 
	else : txt = f'GEX Exp {expDate}'
	drawText(draw, x=x, y=y, txt=txt, color="#3FF")
	drawText(draw, x=x, y=y + (FONT_SIZE), txt="Zero Gamma "+"${:,.2f}".format(zeroG), color="orange")
	drawText(draw, x=x, y=y + (FONT_SIZE * 2), txt="MaxPain ${:,.2f}".format(maxPain), color="#F00")
	pcr = totalPuts / totalCalls
#	color = 'white'
#	if pcr < 0.5 : color = 'green'
#	if pcr > 1.3 : color = 'red'
	color = 'green' if pcr < 0.5 else 'red' if pcr > 1.3 else 'white'
	drawText(draw, x=x, y=y + (FONT_SIZE * 3), txt=f'PCR {round((pcr), 2)}', color="#F00")
	
	img.save("stock-chart.png")
	return "stock-chart.png"

def drawPriceChart(ticker, fileName, gexData, userArgs):
	IMG_W = 400
	IMG_H = 500 + FONT_SIZE + 5
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	txt = fileName.replace('SPY-','').replace('-datalog.json','')
	drawText(draw, x=0, y=0, txt=f'{ticker} {txt} for {", ".join(userArgs)}', color="#0ff")

	#print(1)

	def strikeExists(strikeVal):
		for x in gexData[next(iter(gexData))]['data']:
			#print( x[0], strikeVal )
			if x[0] == strikeVal: return True
		return False
	strikes = []

	#print(2)
	for arg in userArgs:
		strikeVal = int(arg[:-1])
		if arg[-1] == 'c' and strikeExists( strikeVal ) : strikes.append( (strikeVal, 'call') )
		elif arg[-1] == 'p' and strikeExists( strikeVal ) : strikes.append( (strikeVal, 'put') )
	if len(strikes) == 0: return 'error.png'
	#print(3)
	prices = [gexData[t]['price'] for t in gexData]
	maxPrice = max( prices )
	minPrice = min( prices )
	priceDif = maxPrice - minPrice
	if priceDif == 0: priceDif = 1
	#print(4)
	def convertY( val ): return IMG_H - (((val - minPrice) / priceDif) * 500) - 2
	#for i in range(1, len(prices)):
	#	draw.line([i-1, convertY(prices[i-1]), i, convertY(prices[i])], fill="yellow", width=1)
	firstTime = True
	for strike in strikes:
		index = 0
		nex = gexData[next(iter(gexData))]['data']
		for x in range(len(nex)):  #Find the index to the desired strike
			if nex[x][0] == strike[0]: 
				index = x
				break
		element = dp.GEX_CALL_ASK if strike[1] == 'call' else dp.GEX_PUT_ASK
		prices = [gexData[t]['data'][index][element] for t in gexData]
		if firstTime :
			maxPrice = max( prices )
			minPrice = min( prices )
			priceDif = maxPrice - minPrice
			if priceDif == 0: priceDif = 1
			drawRotatedPriceLine(draw, convertY(maxPrice), "green")
			drawText( draw, 50, 30, txt=str( maxPrice ), color="green")
			midPrice = (maxPrice + minPrice) / 2
			drawRotatedPriceLine(draw, convertY(midPrice), "yellow")
			drawText( draw, 50, 250, txt=str( midPrice ), color="yellow")
			drawRotatedPriceLine(draw, convertY(minPrice), "red")
			drawText( draw, 50, IMG_H - 30, txt=str( minPrice ), color="red")
			firstTime = False
		colr = "green" if strike[1] == 'call' else "red"
		for i in range(1, len(prices)):
			draw.line([i-1, convertY(prices[i-1]), i, convertY(prices[i])], fill=colr, width=1)
		
	img.save("price-chart.png")
	return "price-chart.png"

def drawHeatMap(ticker, strikeCount, dayTotal): #Works on any ticker, doesnt use historical data
	def alignValue(val, spaces): return f'{int(val):,d}'.rjust(spaces)

	#pastDays = dp.loadPastDTE() #set to grab -1 dte
	days = dp.getMultipleDTEOptionChain(ticker, dayTotal)
	days = sorted(days, key=lambda x: x[0])
	
	price = dp.getQuote(ticker)
	#candles = dp.getHistory(ticker, 14)
	def findRange( day ): #Used to find range for a previous day
		for candle in candles:
			if candle['date'] == day: 
				return (candle['low'], candle['high'])
		return (0,0)
	#**************************************
	#Build list of strikes to display
	lStrikes = []  
	priceLow = price - strikeCount
	priceHigh = price + strikeCount
	for day in days:
		#print( day )
		for strike in day[1]:
			if (priceLow < strike[0] < priceHigh) and (strike[0] not in lStrikes): lStrikes.append(strike[0])
	lStrikes = sorted(lStrikes)
	count = len(lStrikes)  #done to ensure correct # of strikes are displayed
	
	IMG_W = (len(days) + 1) * 80
	IMG_H = ((count + 2) * (FONT_SIZE + 2)) + 10
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)		
	#*************************************
	#Draw each cell
	x = 0
	for day in days:
		x += 80
		strikes = day[1]
		print(day[0])
		zeroG = dp.calcZeroGEX( strikes )
		maxPain = dp.calcMaxPain( strikes )
		maxCallOI = max(strikes, key=lambda i: i[4])[4]
		maxPutOI = max(strikes, key=lambda i: i[6])[6]
		maxTotalOI = max(strikes, key=lambda i: i[2])[2]
		#maxTotalGEX = max(strikes, key=lambda i: i[1])[1]
		#minTotalGEX = abs(min(strikes, key=lambda i: i[1])[1])
		#maxTotalGEX = max( (maxTotalGEX, minTotalGEX) )
		#dayRange = findRange(day[0])
		#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk
		y = IMG_H - FONT_SIZE - 10
		for displayStrike in lStrikes:
			y -= FONT_SIZE + 2
			strike = (displayStrike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			for val in strikes:
				if val[0] == displayStrike:
					strike = val
					break
			callColor = getColorGradient(maxCallOI, strike[4])
			putColor = getColorGradient(maxPutOI, -strike[6])
			drawRect(draw, x, y, x + 40, y + FONT_SIZE, color=callColor, border='')
			drawRect(draw, x + 41, y, x + 80, y + FONT_SIZE, color=putColor, border='')
			
			if strike[0] == zeroG : drawRect(draw, x, y + FONT_SIZE - 4, x + 80, y + FONT_SIZE, color='yellow', border='')
			if strike[0] == maxPain : drawRect(draw, x, y, x + 80, y + 4, color='grey', border='')			
			#if dayRange[0] < displayStrike < dayRange[1] : drawRect(draw, x, y, x + 10, y + FONT_SIZE, color='blue', border='white')
			
			val = alignValue(strike[2], 8)
			drawText(draw, x=x, y=y, txt=val, color="#F82")
	#***************************************
	#Draw the grid, strikes, and dates
	y2 = FONT_SIZE * 2 
	y = IMG_H - FONT_SIZE - 10
	for j in lStrikes :
		draw.line([0, y, IMG_W, y], fill="white", width=1)
		y -= FONT_SIZE
		drawText(draw, x=0, y=y, txt=str(j), color="#77f")
		y -= 2
	x = 0
	y = IMG_H - FONT_SIZE - 10
	for day in days :
		x += 80
		strDay = day[0].split("-", 1)[1]
		drawText(draw, x=x, y=y, txt="  " + strDay, color="#CCC")
		draw.line([x, y2, x, IMG_H], fill="white", width=1)
	#Draw title for heatmap
	drawRect(draw, 0, 0, IMG_W-2, FONT_SIZE+5, color="#000", border="#CCF")
	drawText(draw, x=0, y=0, txt=f'{ticker} Options Heatmap', color="#0ff")

	img.save("stock-chart.png")
	return "stock-chart.png"

def drawPrecentageHeatMap(ticker, strikeCount, dayTotal):
	def alignValue(val, spaces): return f'{int(val):,d}'.rjust(spaces)

	pastDays = dp.loadPastDTE(-5)  #Currently always pulls last DTE from each day
	days = dp.getMultipleDTEOptionChain(ticker, 5)
	days = sorted(days, key=lambda x: x[0])

	def getDay(day):
		for j in days:
			if j[0] == day: return j
		return -1
	def getStrike(day, strike):
		for s in day:
			if strike == s[dp.GEX_STRIKE] : return s
	
	for pDay in pastDays:   #Change original list to new % data reflecting change over 5dte
		day = getDay(pDay[0])
		if day == -1 : break #return
#		print(f'Match found {pDay[0]} with {day[0]}')
		for strike in pDay[1]:
			tday = getStrike( day[1], strike[dp.GEX_STRIKE] )
			try:
				tday[dp.GEX_TOTAL_OI] = ((strike[dp.GEX_TOTAL_OI] / tday[dp.GEX_TOTAL_OI]) * 100) - 100
				tday[dp.GEX_TOTAL_GEX] = ((strike[dp.GEX_TOTAL_GEX] / tday[dp.GEX_TOTAL_GEX]) * 100) - 100
			except: 
				tday[dp.GEX_TOTAL_OI] = -9990
				tday[dp.GEX_TOTAL_GEX] = -9990
			
	print( f'Total days {len( days )}' )
	price = dp.getQuote(ticker)
	#candles = dp.getHistory(ticker, 14)
	def findRange( day ): #Used to find range for a previous day
		for candle in candles:
			if candle['date'] == day: 
				return (candle['low'], candle['high'])
		return (0,0)
	#**************************************
	#Build list of strikes to display
	lStrikes = []  
	priceLow = price - strikeCount
	priceHigh = price + strikeCount
	for day in days:
		for strike in day[1]:
			if (priceLow < strike[0] < priceHigh) and (strike[0] not in lStrikes): lStrikes.append(strike[0])
	lStrikes = sorted(lStrikes)
	count = len(lStrikes)  #done to ensure correct # of strikes are displayed
	
	IMG_W = (len(days) + 1) * 80
	IMG_H = ((count + 2) * (FONT_SIZE + 2)) + 10
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)		
	#*************************************
	#Draw each cell
	x = 0
	for day in days:
		x += 80
		strikes = day[1]
		#print(day[0])
		zeroG = dp.calcZeroGEX( strikes )
		maxPain = dp.calcMaxPain( strikes )
		maxCallOI = max(strikes, key=lambda i: i[4])[4]
		maxPutOI = max(strikes, key=lambda i: i[6])[6]
		maxTotalOI = max(strikes, key=lambda i: i[2])[2]
		#maxTotalGEX = max(strikes, key=lambda i: i[1])[1]
		#minTotalGEX = abs(min(strikes, key=lambda i: i[1])[1])
		#maxTotalGEX = max( (maxTotalGEX, minTotalGEX) )
		#dayRange = findRange(day[0])
		#0-Strike, 1-TotalGEX, 2-TotalOI, 3-CallGEX, 4-CallOI,  5-PutGEX, 6-PutOI, 7-IV, 8-CallBid, 9-CallAsk, 10-PutBid, 11-PutAsk
		y = IMG_H - FONT_SIZE - 10
		for displayStrike in lStrikes:
			y -= FONT_SIZE + 2
			strike = (displayStrike, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
			for val in strikes:
				if val[0] == displayStrike:
					strike = val
					break
			callColor = getColorGradient(maxCallOI, strike[4])
			putColor = getColorGradient(maxPutOI, -strike[6])
			drawRect(draw, x, y, x + 40, y + FONT_SIZE, color=callColor, border='')
			drawRect(draw, x + 41, y, x + 80, y + FONT_SIZE, color=putColor, border='')
			
			if strike[0] == zeroG : drawRect(draw, x, y + FONT_SIZE - 4, x + 80, y + FONT_SIZE, color='yellow', border='')
			if strike[0] == maxPain : drawRect(draw, x, y, x + 80, y + 4, color='grey', border='')			
			#if dayRange[0] < displayStrike < dayRange[1] : drawRect(draw, x, y, x + 10, y + FONT_SIZE, color='blue', border='white')
			
			val = alignValue(strike[2], 8)
			drawText(draw, x=x, y=y, txt=val, color="#F82")
	#***************************************
	#Draw the grid, strikes, and dates
	y2 = FONT_SIZE * 2 
	y = IMG_H - FONT_SIZE - 10
	for j in lStrikes :
		draw.line([0, y, IMG_W, y], fill="white", width=1)
		y -= FONT_SIZE
		drawText(draw, x=0, y=y, txt=str(j), color="#77f")
		y -= 2
	x = 0
	y = IMG_H - FONT_SIZE - 10
	for day in days :
		x += 80
		strDay = day[0].split("-", 1)[1]
		drawText(draw, x=x, y=y, txt="  " + strDay, color="#CCC")
		draw.line([x, y2, x, IMG_H], fill="white", width=1)
	#Draw title for heatmap
	drawRect(draw, 0, 0, IMG_W-2, FONT_SIZE+5, color="#000", border="#CCF")
	drawText(draw, x=0, y=0, txt=f'{ticker} Options Heatmap', color="#0ff")

	img.save("stock-chart.png")
	return "stock-chart.png"
#drawHeatMap('SPX', 100, 1)