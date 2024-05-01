from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont, Image
import PIL.Image as PILImg
import datapuller as dp
import signals as sig

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

def drawText(draw, x, y, txt, color, anchor = "la"):
	draw.text((x,y), text=txt, fill=color, font=font, anchor=anchor)

def drawRotatedText(img, x, y, txt, color):
	text_layer = PILImg.new('L', (120, FONT_SIZE))
	dtxt = ImageDraw.Draw(text_layer)
	dtxt.text( (0, 0), txt, fill=255, font=font)
	rotated_text_layer = text_layer.rotate(270.0, expand=1)
	PILImg.Image.paste( img, rotated_text_layer, (x,y) )

def drawPointer(draw, y, color = 'yellow'):
	draw.polygon( [290, y, 300, y-10, 300, y+10, 290, y], fill=color, outline='blue')

#function recieves a Tuple Array from datapuller.py
def drawGEXChart(ticker, count, dte, chartType = 0, strikes = None, expDate = 0, price = 0, RAM=False):
	ticker = ticker.upper()
	#print('a')
	if strikes == None:
		optionsChains = dp.getOptionsChain(ticker, dte)
		expDate = optionsChains[0]
		strikes = dp.getGEX(optionsChains[1], chartType=chartType)

	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	strikeLen = len( strikes[0] )
	for strike in strikes:
		for i in range(strikeLen):
			if strike[i] == None : print( strike )
	
	callDollars = sum([strike[dp.GEX_CALL_OI] * strike[dp.GEX_CALL_ASK] for strike in strikes])  # Calc BEFORE shrinking count!!!
	putDollars = sum([strike[dp.GEX_PUT_OI] * strike[dp.GEX_PUT_ASK] for strike in strikes])
	totalCalls = sum([strike[dp.GEX_CALL_OI] for strike in strikes]) 
	totalPuts = sum([strike[dp.GEX_PUT_OI] for strike in strikes]) 
	
	if price == 0: price = dp.getPrice(ticker, strikes)  #Done BEFORE shrinkToCount

	sigs = sig.identifyKeyLevels( strikes )  #Done BEFORE shrinkToCount
	strikes = dp.shrinkToCount(strikes, price, count)
	count = len(strikes)
	
	maxTotalGEX = max(strikes, key=lambda i: i[dp.GEX_TOTAL_GEX])[dp.GEX_TOTAL_GEX]
	minTotalGEX = abs(min(strikes, key=lambda i: i[dp.GEX_TOTAL_GEX])[dp.GEX_TOTAL_GEX])
	maxTotalGEX = max( (maxTotalGEX, minTotalGEX) )
	
	maxTotalOI = max(strikes, key=lambda i: i[dp.GEX_TOTAL_OI])[dp.GEX_TOTAL_OI]
	maxCallVolume = max(strikes, key=lambda i: i[dp.GEX_CALL_VOLUME])[dp.GEX_CALL_VOLUME]
	maxPutVolume = max(strikes, key=lambda i: i[dp.GEX_PUT_VOLUME])[dp.GEX_PUT_VOLUME]
	maxTotalVolume = max( (maxCallVolume, maxPutVolume) )
	maxOIVol = max( (maxTotalOI, maxTotalVolume) )
	
	maxCallGEX = max(strikes, key=lambda i: i[dp.GEX_CALL_GEX])[dp.GEX_CALL_GEX]
	maxPutGEX = abs(min(strikes, key=lambda i: i[dp.GEX_PUT_GEX])[dp.GEX_PUT_GEX])
	maxCallPutGEX = max( (maxCallGEX, maxPutGEX) )
	
	IMG_W = ((FONT_SIZE - 3) * count)   #IMG_W and IMG_H used backwards
	IMG_H = 500 + 65
	IMG_W += 110
	img = PILImg.new("RGB", (IMG_H, IMG_W), "#000")
	draw = ImageDraw.Draw(img)
	#print('g')
	x = IMG_W - 15
	for strike in strikes :
		x -= FONT_SIZE - 3
		strikeColor = "#CCC"
		if strike[dp.GEX_STRIKE] == maxPain : strikeColor = "#F00"
		if strike[dp.GEX_STRIKE] == zeroG : strikeColor = "orange"
		strikeText = str(round((strike[dp.GEX_STRIKE]), 2))	
		drawText(draw, y=x - 5, x=218, txt=strikeText, color=strikeColor)
		#****************
		callVolume = strike[dp.GEX_CALL_VOLUME]
		putVolume = strike[dp.GEX_PUT_VOLUME]
		callOI = strike[dp.GEX_CALL_OI]
		putOI = strike[dp.GEX_PUT_OI]
		if callOI > 0: drawRect(draw, 0, x, ((callOI / maxOIVol) * 65), x + 12, color="#0F0", border='')
		if callVolume > 0: drawRect(draw, 0, x, ((callVolume / maxOIVol) * 65), x + 6, color="#00F", border='')
		if putOI > 0: drawRect(draw, IMG_H - ((putOI / maxOIVol) * 65), x, IMG_H, x + 12, color="#F00", border='')
		if putVolume > 0: drawRect(draw, IMG_H - ((putVolume / maxOIVol) * 65), x, IMG_H, x + 6, color="yellow", border='')
		#***************
		if strike[dp.GEX_TOTAL_GEX] != 0 : drawRect(draw, 215 - ((abs(strike[dp.GEX_TOTAL_GEX]) / maxTotalGEX) * 150), x, 215, x + 12, color=("#0f0" if (strike[dp.GEX_TOTAL_GEX] > -1) else "#f00"), border='')
		if (strike[dp.GEX_CALL_GEX] != 0) : drawRect(draw, 399 - ((strike[dp.GEX_CALL_GEX] / maxCallPutGEX) * 100), x, 399, x + 12, color="#0f0", border='')
		if (strike[dp.GEX_PUT_GEX] != 0) : drawRect(draw, 401, x, 401 - ((strike[dp.GEX_PUT_GEX] / maxCallPutGEX) * 100), x + 12, color="#f00", border='')
		
		if strike[dp.GEX_STRIKE] in sigs[2]: drawPointer( draw, y=x + 6, color='blue' )
		if strike[dp.GEX_STRIKE] in sigs[3]: drawPointer( draw, y=x + 6, color='red' )
		if strike[dp.GEX_STRIKE] in sigs[4]: drawPointer( draw, y=x + 6, color='green' )
	#print('h')
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
	
	colr = "purple"
	txt = "Range Day"
	if sigs[1] == sig.DAY_PUMP :
		colr = "green"
		txt = "PUMP DAY!"
	if sigs[1] == sig.DAY_DUMP :
		colr = "red"
		txt = "DUMP DAY 8p"
	drawText(draw, x=x, y=y + (FONT_SIZE * 3), txt=txt, color=colr)
	#try:
	#	pcr = totalPuts / totalCalls
	#	color = 'green' if pcr < 0.5 else 'red' if pcr > 1.3 else 'white'
	#	drawText(draw, x=x, y=y + (FONT_SIZE * 3), txt=f'PCR {round((pcr), 2)}', color="#F00")
	#except: pass
	
	if RAM : return img
	img.save("stock-chart.png")
	return "stock-chart.png"

def drawPriceChart(ticker, fileName, gexData, userArgs, includePrices = False, RAM=False, deadprice=0.25, minute='630'):
	IMG_W = 1500
	IMG_H = 500 + FONT_SIZE + 15 + 20
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	txt = fileName.replace('0dte-','').replace('-datalog.json','')
	drawText(draw, x=0, y=0, txt=f'{ticker} {txt} for {", ".join(userArgs)}', color="#0ff")
	drawText(draw, x=1400,y=2,txt=minute, color="yellow", anchor="rt")
	maxPrice, minPrice, priceDif = 1, 1, 1
	openTimeIndex = 0
	xPlus = 0
	allPrices = []
	def convertY( val ): return IMG_H - ((val / maxPrice) * 250) - 252 + (xPlus * 5) - 20
	def spxY( val ): return IMG_H - (((val - minPrice) / priceDif) * 500) - 20
	#print('a')
	if 'all' in userArgs:
		strikes = list(gexData.values())[-1]
		for t in gexData: 
			if float(t) // 1 > 630 :
				strikes = gexData[t]
				#print(f'Price chart at {t} - count {len(strikes)}')
				break
		#print('b')
		openPrice = dp.getPrice("SPX", strikes)
		#print('c')
		#targets = dp.findKeyLevels( strikes )
		sigs = sig.identifyKeyLevels( strikes )
		#print( sigs )
		prices = []
		#*******************
		flags = []
		#****************
		allPrices.append(prices)
		firstStrike = gexData[next(iter(gexData))]
		
		callTimes = [[x[dp.GEX_STRIKE], -1] for x in firstStrike if x[dp.GEX_CALL_BID] > deadprice]
		putTimes = [[x[dp.GEX_STRIKE], -1] for x in firstStrike if x[dp.GEX_PUT_BID] > deadprice]
		x = 0
		#print('e')
		for time, strikes in gexData.items():
			minute = float(time)
			callPutPrice = gexData[time][0][dp.GEX_CALL_BID] + gexData[time][0][dp.GEX_PUT_BID]
			if callPutPrice == 0 : continue
			
			if minute < 614 or minute > 631:
				
				currentPrice = dp.getPrice(ticker, strikes)
				prices.append( currentPrice )
				
				mostCallPutVolume = max(strikes, key=lambda i: i[dp.GEX_CALL_VOLUME] + i[dp.GEX_PUT_VOLUME])[dp.GEX_STRIKE]

				flags.append( (minute, mostCallPutVolume) )
				#print(mostCallVolume, mostPutVolume)
				for strike in strikes :
					for c in callTimes:
						if c[1] == -1 and c[0] == strike[dp.GEX_STRIKE] and strike[dp.GEX_CALL_BID] <= deadprice: c[1] = x
					for p in putTimes:
						if p[1] == -1 and p[0] == strike[dp.GEX_STRIKE] and strike[dp.GEX_PUT_BID] <= deadprice: p[1] = x
				x += 1
			else : openTimeIndex = len(prices)
		
		maxPrice = max( (*prices, sigs[0][1]) ) + 5
		minPrice = min( (*prices, sigs[0][0]) ) - 5
		priceDif = maxPrice - minPrice
		
		peaksValleys = dp.findPeaksAndValleys( prices )
		lows = peaksValleys[0]
		highs = peaksValleys[1]
		flag = 0
		
		for x in range(1, len(prices)):
			prevPrice = prices[x-1]
			price = prices[x]
			
			y1 = spxY( prevPrice )
			y2 = spxY( price )
			
			colr = 'yellow'
			for c in callTimes:
				if c[1] == x:
					colr = 'green'
					draw.line([x-7, y2-2, x+7, y2+2], fill="blue", width=4)
					drawText( draw, x, y2, txt=str( c[0] ), color=colr, anchor="rt")
			for p in putTimes:
				if p[1] == x:
					colr = 'red'
					draw.line([x-7, y2-2, x+7, y2+2], fill="blue", width=4)
					drawText( draw, x, y2, txt=str( p[0] ), color=colr, anchor="rt")

			draw.line([x-1, y1, x, y2], fill=colr, width=1)
			
			if x in lows : draw.line((x-20, y2, x+20, y2), fill='red', width=2)
			if x in highs : draw.line((x-20, y2, x+20, y2), fill='green', width=2)
			
#****************************************
			#if flags[x][0] > 700 and flag == 0 and abs(price - flags[x][1]) > 20 :
			#	flag = 1 if price > flags[x][1] else -1
			#if abs(price - flags[x][1]) < 5: flag = 0
			if flag == 1:
				flag = 2
				#drawText( draw, x, y2-40, txt=str( flags[x][1] ), color=colr, anchor="rt")
				draw.polygon( [x,y2-20, x-5,y2-30, x+5,y2-30, x,y2-20], fill='red', outline='blue')
				#print(f'Drawing Put Flag {flags[x][1]} @ {x}x{y2}')
			if flag == -1:
				flag = -2
				#drawText( draw, x, y2+40, txt=str( flags[x][1] ), color=colr, anchor="rt")
				draw.polygon( [x,y2+20, x-5,y2+30, x+5,y2+30, x,y2+20], fill='green', outline='blue')
				#print(f'Drawing Call Flag {flags[x][2]} @ {x}x{y2}')
#****************************************			
			if x == openTimeIndex : 
				draw.line([x, 50, x, 500], fill="purple", width=1)
				if sigs[1] == sig.DAY_PUMP :
					draw.polygon( [x, 250, x-50, 300, x+50, 300, x,250], fill="green", outline='blue')
				if sigs[1] == sig.DAY_DUMP :
					draw.polygon( [x, 250, x-50, 200, x+50, 200, x,250], fill="red", outline='blue')
				
			
		x = 0
		y = FONT_SIZE + 15
		y2 = IMG_H - 2
		while x < 1500:
			draw.line( [x, y, x+2, y], fill="green", width=1)
			draw.line( [x, y2, x+2, y2], fill="red", width=1)
			x += 5
		drawText( draw, 1300, y, txt=str( maxPrice ), color="green", anchor="rt")
		drawText( draw, 1300, y2, txt=str( minPrice ), color="red", anchor="rb")

		for tar in (*sigs[2], *sigs[3], *sigs[4]):#*targets, 
			if minPrice < tar < maxPrice :
				y = spxY( tar )
				colr = "yellow" 
				if tar in sigs[2] : colr = "blue"
				if tar in sigs[3] : colr = "red"
				if tar in sigs[4] : colr = "green"
				draw.line( [0, y, 1500, y], fill=colr, width=1)
				drawText( draw, 1400, y, txt=str(tar), color="yellow", anchor="rb")
		
		if RAM : return (img, allPrices)
		img.save("price-chart.png")
		if includePrices : return ("price-chart.png", allPrices)
		else : return "price-chart.png"  #Below is normal Option Price Chart

	def strikeExists(strikeVal):
		for x in gexData[next(iter(gexData))]:
			#print( x[0], strikeVal )
			if x[0] == strikeVal: return True
		return False
	strikes = []
	
	for arg in userArgs:
		strikeVal = int(arg[:-1])
		if arg[-1] == 'c' and strikeExists( strikeVal ) : strikes.append( (strikeVal, 'call') )
		elif arg[-1] == 'p' and strikeExists( strikeVal ) : strikes.append( (strikeVal, 'put') )
	if len(strikes) == 0: return 'error.png'

	for strike in strikes:
		element = dp.GEX_CALL_BID if strike[1] == 'call' else dp.GEX_PUT_BID
		prices = []
		allPrices.append( prices )
		for t in gexData:
			minute = float(t)
			if minute >= 614 and minute <= 631: 
				openTimeIndex = len(prices)
				continue
			#**************************************************************************************************************************
			#if minute > 700 : continue
			#**************************************************************************************************************************
			callPutPrice = gexData[t][0][dp.GEX_CALL_BID] + gexData[t][0][dp.GEX_PUT_BID]
			if callPutPrice == 0 : continue
			for s in gexData[t]:
				if s[dp.GEX_STRIKE] == strike[0]:
					#if s[element] == 0 : print( t, strike[0], s )
					#if s[element] == 0: print( f'Bad Data {minute}' )
					prices.append( s[element] )
					#if s[element] == 0: print( minute )
					continue			
		
		colr = "green" if strike[1] == 'call' else "red"
		maxPrice = max( prices )
		minPrice = min( prices )
		
		for i in range(1, len(prices)):
			draw.line([i-1, convertY(prices[i-1]), i, convertY(prices[i])], fill=colr, width=1)
			if i == openTimeIndex : draw.line([i, 50, i, 500], fill="purple", width=1)
		
		y = convertY(maxPrice)
		drawRotatedPriceLine(draw, y, colr)
		drawText( draw, 300 + xPlus, y, txt=str( maxPrice ), color=colr, anchor="rt")
		
		y = convertY( minPrice )
		drawRotatedPriceLine(draw, y, colr)
		drawText( draw, 300 + xPlus, y, txt=str( minPrice ), color=colr, anchor="rb")

		"""y = convertY( 0.20 )
		drawRotatedPriceLine(draw, y, colr)
		drawText( draw, 300 + xPlus, y, txt="0.20", color=colr, anchor="rb")"""

		xPlus += 50

	if RAM : return (img, allPrices)
	img.save("price-chart.png")
	if includePrices : return ("price-chart.png", allPrices)
	else : return "price-chart.png"

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
	
def drawWeeklyChart():
	ticker = "SPX"
	count = 40

	IMG_W = ((FONT_SIZE - 3) * count)   #IMG_W and IMG_H used backwards
	IMG_H = 500 + 65
	IMG_W += 110
	img = PILImg.new("RGB", ((IMG_H + 5) * 5, IMG_W), "#000")
	draw = ImageDraw.Draw(img)
	
	images = [
		drawGEXChart(ticker, count, dte=i, expDate=day[0], strikes=day[1], RAM = True)
		for i, day in enumerate(dp.getMultipleDTEOptionChain(ticker, 5))
	]
	for i, dteImage in enumerate(images) :
		x = i * (IMG_H + 5)
		img.paste(dteImage, (x, 0))
		x += IMG_H
		drawRect(draw, x + 1, 0, x + 3, IMG_W, color="#00f", border="yellow")

	img.save("stock-chart.png")
	return "stock-chart.png"
