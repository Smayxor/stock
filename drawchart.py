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

def drawLongPriceLine(draw, y, color, startX, lastX):  #Draws a dashed line
	x = startX
	while x < lastX:
		draw.line([x, y, x + 2, y], fill=color, width=1)
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
	draw.polygon( [280, y, 290, y-10, 290, y+10, 280, y], fill=color, outline='blue')

#function recieves a Tuple Array from datapuller.py
def drawGEXChart(ticker, count, dte, chartType = 0, strikes = None, expDate = 0, price = 0, RAM=False):
	ticker = ticker.upper()
	#print('a')
	if strikes == None:
		optionsChains = dp.getOptionsChain(ticker, dte)
		expDate = optionsChains[0]
		strikes = dp.getGEX(optionsChains[1])
		
	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	strikeLen = len( strikes[0] )
	
	callDollars = sum([strike[dp.GEX_CALL_OI] * strike[dp.GEX_CALL_ASK] for strike in strikes])  # Calc BEFORE shrinking count!!!
	putDollars = sum([strike[dp.GEX_PUT_OI] * strike[dp.GEX_PUT_ASK] for strike in strikes])
	totalCalls = sum([strike[dp.GEX_CALL_OI] for strike in strikes]) 
	totalPuts = sum([strike[dp.GEX_PUT_OI] for strike in strikes]) 
	
	if price == 0: price = dp.getPrice(ticker, strikes)  #Done BEFORE shrinkToCount

	sigs = sig.identifyKeyLevels( strikes )  #Done BEFORE shrinkToCount
	strikes = dp.shrinkToCount(strikes, price, count)
	count = len(strikes)
	
	if chartType == 1 :
		for strike in strikes :
			gamma = strike[dp.GEX_CALL_GEX] / strike[dp.GEX_CALL_OI] if strike[dp.GEX_CALL_OI] > 0 else 0
			strike[dp.GEX_CALL_GEX] = gamma * (strike[dp.GEX_CALL_VOLUME] + strike[dp.GEX_CALL_OI])
			gamma = strike[dp.GEX_PUT_GEX] / strike[dp.GEX_PUT_OI] if strike[dp.GEX_PUT_OI] > 0 else 0
			strike[dp.GEX_PUT_GEX] = gamma * (strike[dp.GEX_PUT_VOLUME] + strike[dp.GEX_PUT_OI]) 
			strike[dp.GEX_TOTAL_GEX] = strike[dp.GEX_CALL_GEX] - strike[dp.GEX_PUT_GEX] #Makes it ABS GEX
	if chartType == 4 :
		for strike in strikes :
			strike[dp.GEX_CALL_GEX] = strike[dp.GEX_CALL_OI] * strike[dp.GEX_CALL_VOLUME]# EGEX conversion
			strike[dp.GEX_PUT_GEX] = -(strike[dp.GEX_PUT_OI] * strike[dp.GEX_PUT_VOLUME])
			strike[dp.GEX_TOTAL_GEX] = strike[dp.GEX_CALL_GEX] - strike[dp.GEX_PUT_GEX] #Makes it ABS GEX
		
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
	maxABSGEX = max( [x[dp.GEX_CALL_GEX] - x[dp.GEX_PUT_GEX] for x in strikes] )
	
	IMG_W = ((FONT_SIZE - 3) * count)   #IMG_W and IMG_H used backwards
	IMG_H = 500 + 65
	IMG_W += 110
	img = PILImg.new("RGB", (IMG_H, IMG_W), "#000")
	draw = ImageDraw.Draw(img)
	#print('g')
	x = IMG_W - 15
	callDeltas, putDeltas = [], []
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
		if strike[dp.GEX_TOTAL_GEX] != 0 : drawRect(draw, 215 - ((abs(strike[dp.GEX_TOTAL_GEX]) / maxTotalGEX) * 150), x, 215, x + 12, color=("#0f0" if (strike[dp.GEX_TOTAL_GEX] > 0) else "#f00"), border='')
		cgexX = (strike[dp.GEX_CALL_GEX] / maxABSGEX) * 150 if (strike[dp.GEX_CALL_GEX] != 0) else 0
		pgexX = (-strike[dp.GEX_PUT_GEX] / maxABSGEX) * 150 if (strike[dp.GEX_PUT_GEX] != 0) else 0
		drawRect(draw, 295, x, 295 + cgexX, x + 12, color="#0f0", border='')
		drawRect(draw, 295 + cgexX, x, 295 + cgexX + pgexX, x + 12, color="#f00", border='')
		
		if strike[dp.GEX_STRIKE] in sigs[2]: drawPointer( draw, y=x + 6, color='blue' )
		if strike[dp.GEX_STRIKE] in sigs[3]: drawPointer( draw, y=x + 6, color='red' )
		if strike[dp.GEX_STRIKE] in sigs[4]: drawPointer( draw, y=x + 6, color='green' )
		if strikeLen == 23 :
			callDeltas.append( (218-(strike[dp.GEX_CALL_DELTA] * 150), x+10) )
			putDeltas.append( (218+(strike[dp.GEX_PUT_DELTA] * 150), x+10) )
	
	if strikeLen == 23 :
		for i in range( 1, len(strikes) ) :
			p1 = callDeltas[i-1]
			p2 = callDeltas[i]
			draw.line([p1[0], p1[1], p2[0], p2[1]], fill="green", width=1)
			p1 = putDeltas[i-1]
			p2 = putDeltas[i]
			draw.line([p1[0], p1[1], p2[0], p2[1]], fill="red", width=1)
	x = 0
	drawText(draw, x=x, y=0, txt=f'{ticker} ' + "${:,.2f}".format(price, 2), color="#3FF")
	drawText(draw, x=x, y=FONT_SIZE * 1, txt="Call OI "+"{:,}".format(totalCalls), color="#0f0")
	drawText(draw, x=x, y=FONT_SIZE * 2, txt="Put OI "+"{:,}".format(totalPuts), color="#f00")
	#drawText(draw, x=x, y=FONT_SIZE * 3, txt="Total "+"{:,.2f}".format(totalCalls-totalPuts), color="yellow")
	#drawText(draw, x=x, y=FONT_SIZE * 1, txt=f'Call OI {totalCalls}', color="#0f0")
	#drawText(draw, x=x, y=FONT_SIZE * 2, txt=f'Put OI {totalPuts}', color="#f00")
	drawText(draw, x=x, y=FONT_SIZE * 3, txt=f'PCR {round(totalPuts/totalCalls, 2)}%', color="yellow")
	y = 0
	x = 260
	if chartType == 1: txt = f'Volume Exp {expDate}' 
	elif chartType == 4: txt = f'EGEX {expDate}' 
	else : txt = f'GEX Exp {expDate}'
	drawText(draw, x=x, y=y, txt=txt, color="#3FF")
	drawText(draw, x=x, y=y + (FONT_SIZE), txt="Zero Gamma "+"${:,.2f}".format(zeroG), color="orange")
	drawText(draw, x=x, y=y + (FONT_SIZE * 2), txt="MaxPain ${:,.2f}".format(maxPain), color="#F00")
	
	colr = "purple"
	txt = "Range Day"
	sigsDay = sigs[1]
	if sigsDay == sig.DAY_PUMP :
		colr = "green"
		txt = "PUMP DAY!"
	elif sigsDay == sig.DAY_DUMP :
		colr = "red"
		txt = "DUMP DAY 8p"
	elif sigsDay == sig.DAY_CRAZY :
		txt = "Crazy GEX"
	elif sigsDay == sig.DAY_CONDOR :
		txt = "Condor Day"
		
	drawText(draw, x=x, y=y + (FONT_SIZE * 3), txt=txt, color=colr)
	
	if RAM : return img
	img.save("stock-chart.png")
	return "stock-chart.png"

def drawPriceChart(ticker, fileName, gexData, userArgs, includePrices = False, RAM=False, deadprice=0.25, timeMinute=630, startTime=0, stopTime=1300):
	IMG_W = 1500
	IMG_H = 705# 500 + FONT_SIZE + 15 + 20
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	txt = fileName.replace('0dte-','').replace('-datalog.json','')
	drawText(draw, x=0, y=0, txt=f'{ticker} {txt} for {", ".join(userArgs)}', color="#0ff")
	drawText(draw, x=1400,y=2,txt=str(timeMinute), color="yellow", anchor="rt")
	allPrices = []
	displayStrikes = []
	flags = []
	#totalCallVolume = []
	#totalPutVolume = []
	openTimeIndex = 0

	try :
		startTime = int(startTime)
		stopTime = int(stopTime)
	except :
		startTime = 0
		stopTime = 1300
	if startTime > 1200 : startTime = 1200
	if stopTime < startTime : stopTime = startTime + 100
	ft = 631 if startTime < 631 else startTime
	
	firstTime = min( gexData.keys(), key=lambda i: abs(ft - float(i)))
	#print(f'drawPriceChart {firstTime}')
	firstStrikes = gexData[firstTime]
	sigs = sig.identifyKeyLevels( firstStrikes )
	#print( sigs )
	EMA_PERIOD = int(deadprice * 100)
	EMA_PERIOD2 = int((deadprice*10000)%100)
	strat = sig.Signal(firstTime=firstTime, strikes=firstStrikes, deadprice=deadprice, ema1=EMA_PERIOD, ema2=EMA_PERIOD2)
	dataIndex = 9999
	#strat = sig.Signal(firstTime=firstTime, strikes=firstStrikes, deadprice=deadprice)
	
	for arg in userArgs:
		if arg == 'spx' :
			displayStrikes.append( ('spx', 0) )
			continue
		if arg == 'all' :
			displayStrikes.append( ('all', 0) )
			break
		strikeText = int(arg[:-1])
		strikeStrike = next((x for x in firstStrikes if x[dp.GEX_STRIKE] == strikeText), ['spx'])[dp.GEX_STRIKE]
		displayStrikes.append( (strikeStrike, 'call' if arg[-1] == 'c' else 'put') )
	
	lenDisplays = len(displayStrikes)
	if lenDisplays == 0: return 'error.png'
	dStrike1 = displayStrikes[0]
	dStrike2 = None if lenDisplays == 1 else displayStrikes[1]
	#print( dStrike1, dStrike2 )
	prices1 = []
	prices2 = []
	
	for t, strikes in gexData.items():
		minute = float(t)
		if not (startTime < minute < stopTime) : continue
		callPutPrice = gexData[t][0][dp.GEX_CALL_BID] + gexData[t][0][dp.GEX_PUT_BID] #filtering out bad data
		if callPutPrice == 0 : continue
		if minute > 614 and minute < 631 : 
			openTimeIndex = len(prices1)
			continue
		spxPrice = dp.getPrice("SPX", strikes)
		flags.append( strat.addTime(minute, strikes) )
		if timeMinute == t : dataIndex = len(flags)
		if dStrike1[0] == 'all' or dStrike1[0] == 'spx' : 
			prices1.append(spxPrice)
		else:
			element = dp.GEX_CALL_BID if dStrike1[1] == 'call' else dp.GEX_PUT_BID
			bid = next((x for x in strikes if x[dp.GEX_STRIKE] == dStrike1[0]))[element]
			prices1.append(bid)
		if dStrike2 != None : 
			if dStrike2[0] == 'spx' : prices2.append(spxPrice)
			else:
				element = dp.GEX_CALL_BID if dStrike2[1] == 'call' else dp.GEX_PUT_BID
				bid = next((x for x in strikes if x[dp.GEX_STRIKE] == dStrike2[0]))[element]
				prices2.append(bid)
	allPrices.append( prices1 )
	if lenDisplays == 2 : allPrices.append( prices2 )
	
	displaySize = 600
	if lenDisplays == 2 : displaySize = 300
	
	lows, highs, spxPrices = [], [], None
	if dStrike1[0] == 'all' or dStrike1[0] == 'spx' : spxPrices = prices1
	if dStrike2 != None and (dStrike2[0] == 'all' or dStrike2[0] == 'spx') : spxPrices = prices2
	if spxPrices != None :
		peaksValleys = sig.findPeaksAndValleys( spxPrices )
		lows = peaksValleys[0]
		highs = peaksValleys[1]

	def convertY( val, maxPrice ): return displaySize - ((val / maxPrice) * displaySize)
	yValues = ([],[])
	for j in range(lenDisplays):
		prices = allPrices[j]
		smays = strat.EMAs1
		smays2 = strat.EMAs2
	
		lenPrices = len(prices)
		if lenPrices < 2 : break
		maxPrice, maxSPX = max( prices ), 0
		minPrice, minSPX = min( prices ), 0
		colr = 'yellow' 
		isSPX = displayStrikes[j][0] == 'spx' or displayStrikes[j][0] == 'all'
		
		if isSPX :
			maxPrice = max( (*prices, sigs[0][1]) ) + 5
			minPrice = min( (*prices, sigs[0][0]) ) - 5
			maxSPX = maxPrice
			minSPX = minPrice
			maxPrice = maxPrice - minPrice
		else :
			if displayStrikes[j][1] == 'call' : colr = 'green'
			else: colr = 'red'
		addY = 30 + (j * 302)
		if displaySize == 600 : addY = 30
		yValues[j].append( prices[0] - minPrice)
		for x in range( 1, lenPrices ) :
			price = prices[x]
			prevPrice = prices[x-1]
		
			if isSPX :
				price = price - minPrice
				prevPrice = prevPrice - minPrice
			
			y1 = convertY( prevPrice, maxPrice ) + addY
			y2 = convertY( price, maxPrice ) + addY
			yValues[j].append(y2)
			
			for c in strat.callTimes:
				if c[1] == x:
					cr = 'green'
					draw.line([x-7, y2-2, x+7, y2+2], fill="blue", width=4)
					drawText( draw, x, y2, txt=str( c[0] ), color=cr, anchor="rb")
			for p in strat.putTimes:
				if p[1] == x:
					cr = 'red'
					draw.line([x-7, y2-2, x+7, y2+2], fill="blue", width=4)
					drawText( draw, x, y2, txt=str( p[0] ), color=cr, anchor="rt")
			
			draw.line([x-1, y1, x, y2], fill=colr, width=1)
			

			def drawEMA( emas, period, ema_color ): #*************** Draw EMA ******************
				pp = emas[x-period-1] - minPrice
				p = emas[x-period] - minPrice
				y3 = convertY( pp, maxPrice ) + addY
				y4 = convertY( p, maxPrice ) + addY
				draw.line([x-1, y3, x, y4], fill=ema_color, width=1)
			if x > EMA_PERIOD and smays != None : drawEMA( smays, EMA_PERIOD, "purple" )
			if x > EMA_PERIOD2 and smays2 != None : drawEMA( smays2, EMA_PERIOD2, "aqua" )
			
			flag = flags[x]
			if flag == -1: draw.polygon( [x,y2-20, x-5,y2-30, x+5,y2-30, x,y2-20], fill='red', outline='blue')
			if flag == 1: draw.polygon( [x,y2+20, x-5,y2+30, x+5,y2+30, x,y2+20], fill='lime', outline='green')
			
			if x == openTimeIndex : 
				draw.line([x, 50, x, 600], fill="purple", width=1)
				#if sigs[1] == sig.DAY_PUMP :
				#	draw.polygon( [x, 250, x-50, 300, x+50, 300, x,250], fill="green", outline='blue')
				#if sigs[1] == sig.DAY_DUMP :
				#	draw.polygon( [x, 250, x-50, 200, x+50, 200, x,250], fill="red", outline='blue')
				
				ovnPrices = prices[:openTimeIndex]
				ovnl = min( ovnPrices )
				ovnh = max( ovnPrices )
				txtl = ' ${0:.2f}'.format(ovnl)
				txth = ' ${0:.2f}'.format(ovnh)
				if isSPX : 
					ovnl = ovnl - minPrice
					ovnh = ovnh - minPrice
				y = convertY( ovnl, maxPrice ) + addY
				
				drawLongPriceLine(draw, y, 'orange', 0, openTimeIndex)
				drawText( draw, 0, y, txt=txtl, color='orange', anchor="lt")

				y = convertY( ovnh, maxPrice ) + addY
				
				drawLongPriceLine(draw, y, 'orange', 3, openTimeIndex)
				drawText( draw, 0, y, txt=txth, color='orange', anchor="lt")
			
			if x in lows : draw.line((x-20, y2, x+20, y2), fill='red', width=2)
			if x in highs : draw.line((x-20, y2, x+20, y2), fill='green', width=2)

		
		txt = str( max((maxPrice, maxSPX)) )
		y = convertY(maxPrice, maxPrice) + addY
		drawLongPriceLine(draw, y, colr, 1, 1400)
		drawText( draw, 1200 + (j*50), y, txt=txt, color=colr, anchor="rt")
		
		txt = str( max( (minPrice, minSPX) ) )
		lower = 0
		if not isSPX : lower = minPrice
		y = convertY( lower, maxPrice ) + addY
		drawLongPriceLine(draw, y, colr, 3, 1400)
		drawText( draw, 1200 + (j*50), y, txt=txt, color=colr, anchor="rb")
		
		if isSPX : # Draw lines every 25 points on SPX
			maxMultiple = (int(maxSPX // 25) +1) * 25
			minMultiple = (int(minSPX // 25) +1) * 25
			for spxVal in range( minMultiple, maxMultiple, 25 ) : 
				y = convertY( spxVal - minPrice, maxPrice ) + addY
				drawLongPriceLine(draw, y, 'purple', 1, 1400)
				drawText( draw, 1200 + (j*50), y, txt=str(spxVal), color='purple', anchor="rb")
		
		#***********************************Display High and Low price within range of Mouse Hover *********************************
		sliceStart = dataIndex - 30 if dataIndex - 30 > 0 else 0
		if sliceStart > lenPrices - 30 : sliceStart = 0#lenPrices - 30
		sliceStop = dataIndex + 30 if dataIndex + 30 < lenPrices else lenPrices
		preData = prices[sliceStart:sliceStop]
		def drawHighLow(hlIndex, anch):
			txt = '${0:.2f}'.format(preData[hlIndex])
			y = preData[hlIndex]
			if isSPX : y = y - minPrice
			y = convertY( y, maxPrice ) + addY
			sspiX = sliceStart+hlIndex
			drawLongPriceLine(draw, y, 'orange', sspiX-50, sspiX+50)
			drawText( draw, sspiX, y, txt=txt, color='orange', anchor=anch)
		drawHighLow( preData.index(min(preData)), "rt")
		drawHighLow( preData.index(max(preData)), "rb")
		#************************************* END High Low Display ************************************
		
		#self.Straddles = sigs[2] 	#self.PutWalls = sigs[3]    #self.CallWalls = sigs[4]    #self.AllNodes = sigs[2] + sigs[3] + sigs[4]	
		if isSPX :
			for tar in sigs[2] + sigs[3] + sigs[4]:
				if minSPX < tar < maxSPX :
					y = convertY( tar - minSPX, maxPrice ) + addY
					colr = "yellow" 
					if tar in sigs[2] : colr = "blue"
					if tar in sigs[3] : colr = "red"
					if tar in sigs[4] : colr = "green"
					#draw.line( [0, y, 1500, y], fill=colr, width=1)
					drawLongPriceLine(draw, y, colr, 3, 1400)
					drawText( draw, 1400, y, txt=str(tar), color="yellow", anchor="rb")
			"""
			#*************************Displays MostCommonPrices - FakeVolumeProfile ********************************
			for mcp in strat.MostCommonPrices :
				y = convertY( mcp[0] - minSPX - 0.5, maxPrice ) + addY
				y2 = convertY( mcp[0] - minSPX + 0.5, maxPrice ) + addY
				colr = 'blue'
				drawRect(draw, 1400 - mcp[1], y, 1400, y2, color="#00f", border='')
			"""
	h = 650
	for x in range( 30, strat.getVolumeDeltaLen() ) :  # *****************Volume Chart under the SPX chart****************************
		dif = strat.getVolumeDelta(x)
		cr = 'green' if dif > 0 else 'red'
		y2 = abs(dif) / 500
		draw.line([x, 700-y2, x, 700], fill=cr, width=1)
	
	if isSPX == 5 :	#*****************************************Displays volume chart above *************************************
		timeMinute = float(timeMinute)
		times = gexData.keys()
		lenTimes = len( times )
		firstTime = min( times, key=lambda i: abs(timeMinute - float(i))) #**********Set to mouse cursor
		firstStrikes = gexData[firstTime]
		lenStrikes = len(firstStrikes)
		newList = []
		def grabTotal(index): return firstStrikes[index][dp.GEX_CALL_VOLUME] + firstStrikes[index][dp.GEX_PUT_VOLUME]		
		for i, strike in enumerate(firstStrikes) :
			if i == 0 or i > lenStrikes-2:
				newList.append(0)
				continue
			pre = grabTotal(i-1)
			now = grabTotal(i)
			post = grabTotal(i+1)
			dif = abs(now - ((pre + post) / 2))
			newList.append(now)
		maxNL = max(newList)
		for i, strike in enumerate(firstStrikes) :
			txt = '\n'.join([*str(strike[dp.GEX_STRIKE]).split('.')[0]])
			x = (i * FONT_SIZE) + FONT_SIZE
			y = 50
			draw.multiline_text((x,y), txt)	
			#callV = strike[dp.GEX_CALL_VOLUME]
			#putV = strike[dp.GEX_PUT_VOLUME]
			#totalV = (callV + putV) / 100
			y = ((newList[i] / maxNL) * 100)
			draw.line([x, 110, x, 110+y], fill='blue', width=10)
		
	if len(strat.ExtraDisplayText) > 0 :
		draw.multiline_text((1200,50), strat.ExtraDisplayText)	
			
	if RAM : return (img, allPrices, yValues)
	img.save("price-chart.png")
	if includePrices : return ("price-chart.png", allPrices)
	else : return "price-chart.png"  #Below is normal Option Price Chart


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

def drawCustomChart(ticker, fileName, gexData, userArgs, includePrices=False, RAM=True, deadprice=0.30, timeMinute=630):
	IMG_W = 1500
	IMG_H = 705# 500 + FONT_SIZE + 15 + 20
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	txt = fileName.replace('0dte-','').replace('-datalog.json','')
	drawText(draw, x=0, y=0, txt=f'{ticker} {txt} for {", ".join(userArgs)}', color="#0ff")
	drawText(draw, x=1400,y=2,txt=str(timeMinute), color="yellow", anchor="rt")
	allPrices = []
	displayStrikes = []
	flags = []
	totalCallVolume = []
	totalPutVolume = []
	openTimeIndex = 0
	firstTime = min( gexData.keys(), key=lambda i: abs(630 - float(i)))
	firstStrikes = gexData[firstTime]
	sigs = sig.identifyKeyLevels( firstStrikes )
	strat = sig.SignalDataRelease(firstTime=firstTime, strikes=firstStrikes, deadprice=deadprice)
	dataIndex = 9999
	
	timeMinute = float(timeMinute)
	times = gexData.keys()
	lenTimes = len( times )
	firstTime = min( times, key=lambda i: abs(timeMinute - float(i)))
	firstStrikes = gexData[firstTime]
	#sigs = sig.identifyKeyLevels( firstStrikes )
	#strat = sig.SignalDataRelease(firstTime=firstTime, strikes=firstStrikes, deadprice=deadprice)
	spxPrices = [dp.getPrice("SPX", strikes) for strikes in gexData.values()]
	yValues = ([50 for x in spxPrices],[])

	for i, strike in enumerate(firstStrikes) :
		txt = '\n'.join([*str(strike[dp.GEX_STRIKE])])
		x = (i * FONT_SIZE) + FONT_SIZE
		y = 500
		draw.multiline_text((x,y), txt)

	
	allPrices = []
	allPrices.append(spxPrices)
	if RAM : return (img, allPrices, yValues)
	img.save("price-chart.png")
	if includePrices : return ("price-chart.png", allPrices)
	else : return "price-chart.png"  #Below is normal Option Price Chart
