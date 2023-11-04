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
def drawGEXChart(ticker, count, dte):
	ticker = ticker.upper()
	optionsChains = dp.getOptionsChain(ticker, dte)
	expDate = optionsChains[0]
	strikes = dp.getGEX(optionsChains[1])
	atr = dp.getATR(ticker)
	atrs = atr[1]
	zeroG = dp.calcZeroGEX( strikes )
	maxPain = dp.calcMaxPain( strikes )
	callDollars = sum([strike[4] * strike[9] for strike in strikes])  # Calc BEFORE shrinking count!!!
	putDollars = sum([strike[6] * strike[11] for strike in strikes])

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
			if atrs[i] == strike[0]: 
				strikeText = str(round(atrs[i], 1))	
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
	drawText(draw, x=x, y=y, txt=f'GEX Exp {expDate}', color="#3FF")
	drawText(draw, x=x, y=y + (FONT_SIZE), txt="Zero Gamma "+"${:,.2f}".format(zeroG), color="orange")
	drawText(draw, x=x, y=y + (FONT_SIZE * 2), txt="MaxPain ${:,.2f}".format(maxPain), color="#F00")
	
	img.save("stock-chart.png")
	return "stock-chart.png"
"""
			for kl in keyLevels:
				if strike == kl: drawPointer(draw, 218 + font.getmask(str(strike)).getbbox()[2], x + 8, "#77F")
			if strike == strikes.ClosestStrike: drawPointer(draw, 218 + font.getmask(str(strike)).getbbox()[2], x + 8, "#FF7")
		y = 0
		if chartType == CHART_ROTATE :
			x = x + 280
		else: 
			y = FONT_SIZE * 5
"""
