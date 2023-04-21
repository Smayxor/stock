#Open this url in a browser, it directs you to TDA login page, HTTP server running fetches the Auth Code, and retrieves Auth/Refresh tokens.  You can disable the HTTPServer for 90 days if wanted
#https://auth.tdameritrade.com/oauth?client_id=(YOUR_API_KEY_HERE)%40AMER.OAUTHAP&response_type=code&redirect_uri=https%3A%2F%2Flocalhost%3A8080%2F


#	This software is completely free to use, modify, or anything else you want
#	Copyright (C) 2022 Seth Mayberry

#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.

#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.

#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <https://www.gnu.org/licenses/>.

#Version 1.7 Switched the way data was being stored to using Classes. Redid code for drawing charts, so it's easier to add different chart types
#Version 1.6 Completely discord based.  Removed all GUI code.  Lots of bug fixes and new features
#Version 1.5 Managed to get OAUTH tokens working.  Only drawing on PIL Image, and copying to TKinter Canvas. Rotated strikes prices. Moved lots of data to fundamentals area.  Still need to bot the login page!
#Version 1.4 Made images larger,  gave bot more !commands.  renamed to .py instead of .pyt.  included yahoo finance library yfinance to get company fundamentals.  fundamentals are now "Rated" and colored from Red to Green (rating system needs an overhaul).  Server Mode and GUI Mode option from command prompt
#Version 1.3  Added DISCORD BOT functionality.  Make account in Discord Developer, add an App, give Read Messages,  Send Message, Attach Files permissions.  Add a BOT_TOKEN to the apikey.json
#Version 1.2  Got it to save chart as a png.  Preparing for a discord bot
#Version 1.1  Improved display of data on charts to scale with max values

#from datetime import date
import datetime
import time
import requests
import json
import math
import os
import threading
import sys
import random
import csv
from urllib.parse import unquote as unenc
from urllib.parse import quote as enc
from os.path import exists
from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont
import PIL.Image as PILImg
from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands
from itertools import accumulate
import re

#************************************************************
#Get API Key from TDA Developer Account new App,  place in file named apikey.json with this for contents-> {"API_KEY": "your-key-here"}
init = json.load(open('apikey.json'))
MY_API_KEY = init['API_KEY']
BOT_TOKEN = init['BOT_TOKEN']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
BOT_APP_ID = init['DISCORD_APP_ID']
BOT_CLIENT_ID = init['BOT_CLIENT_ID']
TENOR_API_KEY = init['TENOR_API_KEY']
#POLYGON_API_KEY = init['POLYGON']#DISCORD_ID = init['DISCORD_APP_ID']#DISCORD_KEY = init['DISCORD_API_KEY']#BOT_ID = init['BOT_CLIENT_ID']#BOT_SECRET = init['BOT_SECRET']
#************************************************************

#Declarations for various TDA API URLs to fetch JSON data on stocks
endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?apikey={api_key}"
vix_endpoint = "https://api.tdameritrade.com/v1/marketdata/%24VIX.X/quotes?apikey={api_key}"   # %24 is a $  aka $VIX.X
options_endpoint = "https://api.tdameritrade.com/v1/marketdata/chains?apikey={api_key}&symbol={stock_ticker}&contractType=ALL&strikeCount={count}&includeQuotes=FALSE&strategy=SINGLE&range=ALL&toDate={toDate}"
fundamental_endpoint = "https://api.tdameritrade.com/v1/instruments?apikey={api_key}&symbol={stock_ticker}&projection=fundamental"
price_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?apikey={api_key}"   # %24 is a $  aka $VIX.X
auth_endpoint = "https://api.tdameritrade.com/v1/oauth2/token?apikey={api_key}"
history_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&periodType=day&period=1&frequencyType=minute&frequency=1&needExtendedHoursData=true"
atr_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&periodType=month&period=1&frequencyType=daily&frequency=1&needExtendedHoursData=false"
atr2_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&endDate={end_date}&startDate={start_date}&needExtendedHoursData=true"
CHART_GEX = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_DAILYIV = 3
CHART_ROTATE = 4
CHART_JSON = 5
CHART_ATR = 6
CHART_LASTDTE = 7
CHART_LOG = 8
CHART_CHANGE = 9
CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "DAILY IV ", "GEX ", "JSON ", "ATR+FIB ", "LAST DTE ", "LOG-DATA ", "CHANGE IN GEX "]
storedStrikes = []

FONT_SIZE = 22
STR_FONT_SIZE = str(int(FONT_SIZE / 2))  #strangely font size is 2x on tkinter canvas
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic") #Place font file in same folder, or use supply path if needed in Linux

IMG_W = 1000
IMG_H = 500
#IVUpdateChannel = []
#IVUpdateChannelCounter = 0

HEADER = {
	'Accept': '*/*',
	'Accept-Encoding': 'gzip',
	'Accept-Language': 'en-US',
	'Authorization': 'None',
	'Host': 'api.tdameritrade.com',
	'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 15183.59.0) AppleWebKit/537.36 (KHTML'
}
SERVER_HEADER = {  #can optionally pop/remove the Authorization field from HEADER
	"Content-Type": "application/x-www-form-urlencoded"
}
oauth_params = {
	'grant_type': 'authorization_code',
	'refresh_token': '',
	'access_type': 'offline',
	'code': '',
	'client_id': MY_API_KEY + '@AMER.OAUTHAP',
	'redirect_uri': 'https://localhost:8080/',
	'apikey': MY_API_KEY
}

"""   **********Uncomment this section to enable HTTPServer to catch Auth Token and Refresh Token from Auth Code ***********
* This is the server for the redirect URL.  You will have to run the link at top of this file in a web browser to login to TDA Account *
#fetches new access tokens
def serverOAUTH():
	#for redirect url, to fetch tokens
	import socket
	import ssl
	from http.server import HTTPServer, BaseHTTPRequestHandler

	class requesthandler(BaseHTTPRequestHandler):
		def do_GET(self):
			#print("Got Code = ", self.path)
			self.send_response(200)
			self.send_header("Content-type","text/html")
			self.end_headers()
			self.wfile.write("<html><body>It works</body></html>".encode('utf8'))
			if "code=" in self.path:
				code = unenc( self.path.split(str('code='))[1] )# unenc()
				print(code)
				oauth_params['code'] = code
				oauth_params['grant_type'] = 'authorization_code'
				oauth_params['refresh_token'] = ''
				oauth_params['access_type'] = 'offline'
				oauth_params['redirect_uri'] = 'https://localhost:8080/'
				page = requests.post(url=auth_endpoint.format(api_key=MY_API_KEY), headers=SERVER_HEADER, data=oauth_params)
				print(unenc(page.content))
				with open("access-token.json", "w") as outfile:
					outfile.write(unenc(page.content))
					loadAccessTokens()

	httpd = HTTPServer(('127.0.0.1', 8080), requesthandler)
	httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='./example.key', certfile='./example.crt', server_side=True)
	httpd.serve_forever()
serverSockThread = threading.Thread(target=serverOAUTH)
serverSockThread.start()
"""

ACCESS_TOKEN = ""
REFRESH_TOKEN = ""

def loadAccessTokens():
	if exists('access-token.json'):
		init = json.load(open('access-token.json', 'rb'))
		if 'access_token' in init:
			ACCESS_TOKEN = init['access_token']
			REFRESH_TOKEN = init['refresh_token']
			HEADER['Authorization'] = "Bearer " + ACCESS_TOKEN
#loadAccessTokens()

def refreshTokens():
	if exists('access-token.json'): 
		init = json.load(open('access-token.json', 'rb'))
		if 'refresh_token' in init:
			REFRESH_TOKEN = init['refresh_token']
	oauth_params['grant_type'] = 'refresh_token'
	oauth_params['refresh_token'] = REFRESH_TOKEN
	oauth_params['access_type'] = ''
	oauth_params['redirect_uri'] = ''
	oauth_params['code'] = ''
	#When Refresh Token ultimately times out, this method will fail in 90 days   *******************************
	page = unenc(requests.post(url="https://api.tdameritrade.com/v1/oauth2/token", headers=SERVER_HEADER, data=oauth_params).content)
	merge = "{\n  \"refresh_token\": \"" + REFRESH_TOKEN + "\", \n  \"refresh_token_expires_in\": " + str(init['refresh_token_expires_in']) + ", " + page.split("{")[1]
	with open("access-token.json", "w") as outfile:
		outfile.write(merge)
	loadAccessTokens()
refreshTokens()

#Declarations for slash commands
url = "https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands"
headers = { "Authorization": "Bot " + BOT_TOKEN}
slash_command_json = {
	"name": "gex", "type": 1, "description": "Draw a GEX/DEX chart", "options": [ { "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, { "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, { "name": "count", "description": "Strike Count", "type": 4, "required": False }, { "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [{ "name": "Normal", "value": "Normal"  }, { "name": "Rotated", "value": "R" }, { "name": "Volume", "value": "V" }, { "name": "LastDTE", "value": "LD"  }, { "name": "IV", "value": "IV"  }, { "name": "DailyIV", "value": "DAILYIV"  }, { "name": "JSON", "value": "JSON"  }, { "name": "ATR", "value": "ATR"  }, { "name": "CHANGE", "value": "CHANGE"  }]}   ] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "8ball", "type": 1, "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "sudo", "type": 1, "description": "Stuff you cant do on Smayxor", "options":[{ "name": "command", "description": "Super User ONLY!", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "news", "type": 1, "description": "Gets todays events"}
print( requests.post(url, headers=headers, json=slash_command_json) )

#Removes slash commands
#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/COMMAND_ID", headers=headers) )

def getTenorGIF( search ):
	url ="https://g.tenor.com/v2/search?q=%s&key=%s&limit=%s" % (search, TENOR_API_KEY, "8")
	r = requests.get(url=url)
	content = json.loads(r.content)
	dctResults = []
	if r.status_code == 200:
		for ids in content['results']:
			dctResults.append( ids['media_formats']['tinygif']['url'] )
		return random.choice( dctResults )
	else: return "https://media.tenor.com/F2clNh5qPRoAAAAM/pump-stocks.gif"

gms = [enc("gm friends"), enc("good morning"), enc("wake up"), enc("time to work")]
pumps = [enc("stock pump rocket moon"), enc("stock bull"), enc("pepe money rain")]
dumps = [enc("stock dump crash"), enc("bear stock")]
titties = [enc("boobs bounce breast"), enc("women motorboat boobs"), enc("asian tits")]
asses = [enc("women ass twerk poggers"), enc("women sexy butt"), enc("latina big ass")]
		
class MyNewHelp(commands.MinimalHelpCommand):
	async def send_pages(self):
		strHelp = """}? for commands for Smayxor
}s ticker dte, you can leave out DTE for 0DTE.  Can also use /gex ticker dte charttype
/8ball followed by a question, ending in ?
The top bars are OI.
The Red/Green bars above the strikes are Total Gamma Exposure, with blue/pink DEX lines.
Under the strikes is Call Put GEX individually
Additional Chart Types are V for volume, IV for ImpliedVolatility, R for rotated, and TV for TimeValue
}s spx 0 v	for a volume chart
Smayxor has switched to using /gex
}gm }tits }ass }pump }dump also exist"""
		destination = self.get_destination()
		for page in self.paginator.pages:
#			emby = discord.Embed(description=page)
#			await destination.send(embed=emby)
			await destination.send(strHelp)
tickers = []
counter = 0
auto_updater = []
updateRunning = False
update_timer = 300
blnFirstTime = True
bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyNewHelp(), sync_commands=True)
def thread_discord():
	def getChartType( arg ):
		arg = arg.upper()
		if arg == 'V': return CHART_VOLUME
		elif arg == 'IV': return CHART_IV
		elif arg == 'DAILYIV': return CHART_DAILYIV
		elif arg == 'R': return CHART_ROTATE
		elif arg == 'JSON': return CHART_JSON
		elif arg == 'ATR': return CHART_ATR
		elif arg == 'LD': return CHART_LASTDTE
		elif arg == 'CHANGE': return CHART_CHANGE
		else: return CHART_GEX

	@bot.tree.command(name="gex", description="Draws a GEX chart")
	async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, count: int = 40, chart: str = "R"):
		global tickers, updateRunning#, auto_updater, counter, CallATMIV, PutATMIV, IVUpdateChannel, IVUpdateChannelCounter
		ticker = ticker.upper()
		if count < 2 : count = 2
		await intr.response.send_message("Fetching " + CHARTS_TEXT[getChartType(chart)] + " chart for " + ticker + " " + str(dte) + "DTE")
		tickers.append( (ticker, dte, count, getChartType(chart), intr.channel.id, intr.channel) )
#		if updateRunning == False :
#			print("Starting queue")
#			updateRunning = True
#			channelUpdate.start()

	@bot.command(name="pump")
	async def command_pump(ctx, *args): await ctx.send( getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
	@bot.command(name="dump")
	async def command_dump(ctx, *args): await ctx.send( getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )
	@bot.command(name="tits")
	async def command_tits(ctx, *args): await ctx.send( getTenorGIF( random.choice(titties) + enc(" " + ' '.join(args)) ) )
	@bot.command(name="ass")
	async def command_ass(ctx, *args): await ctx.send( getTenorGIF( random.choice(asses) + enc(" " + ' '.join(args)) ) )
	@bot.command(name="gm")
	async def command_gm(ctx, *args): await ctx.send( getTenorGIF( random.choice(gms) + enc(" " + ' '.join(args)) ) )
	
	@bot.tree.command(name="8ball", description="Answers your question?")
	async def slash_command_8ball(intr: discord.Interaction, question: str):
		future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good']
		if "?" in question: await intr.response.send_message("Question: " + question + "\rAnswer: " + random.choice(future))
		else: await intr.response.send_message("Please phrase that as a question")

	@bot.tree.command(name="news")
	async def slash_command_news(intr: discord.Interaction):
		await intr.response.send_message(fetchEvents())

	@bot.tree.command(name="sudo")
	@commands.is_owner()
	async def slash_command_sudo(intr: discord.Interaction, command: str):
		global tickers, updateRunning, auto_updater, update_timer#, counter, CallATMIV, PutATMIV, IVUpdateChannel, IVUpdateChannelCounter
		user = str(intr.user)
		args = command.upper().split(' ')
		print( args )
		if BOT_USER_FOR_KILL != user:
			await intr.response.send_message(user + " you can't kill meme!")
			return
		elif args[0] == "KILL" :
			await intr.response.send_message(user + " triggered shutdown")
			await bot.close()
			await bot.logout()
			exit(0)
		elif args[0] == "START" :
			print("starting")
			dte = args[2] if (len(args) > 2) and args[2].isnumeric() else '0'
			count = args[3] if (len(args) > 3) and args[3].isnumeric() else '40'
			chart = getChartType(args[4]) if (len(args) > 4) else CHART_GEX
			update_timer = int(args[5]) if (len(args) > 5) and args[5].isnumeric() else 300
			print("Appending to Auto_Updater array :", args[1], dte, "-dte", count, "-strikes", chart, intr.channel.id, update_timer, "-seconds")
			auto_updater.append( (args[1], dte, count, chart, intr.channel.id, intr.channel) )
			await intr.response.send_message(user + " started auto-update on " + args[1] + " " + str(dte) + "dte " + str(count) + "-strikes " + str(chart) + "-Chart " + str(update_timer) + " seconds" )
		elif args[0] == "STOP" :
			auto_updater.clear()
			await intr.response.send_message(user + " stopped auto-updater")
		elif args[0] == "UPDATE" :
			await intr.response.send_message(user + " requested code update")
			print("getting update")
			r = requests.get(url="https://raw.githubusercontent.com/Smayxor/stock/main/oauth.py")
			print("recieved file")
			with open("oauth.py", "wb") as outfile:
				outfile.write(r.content)
			exit(9)
			await bot.close()
			await bot.logout()
		elif args[0] == "LOGIV":
			await intr.response.send_message(user + " loggin IV data manually")
			logData("SPX")
			logData("SPY")
		elif args[0] == "CLEAR":
			await intr.response.send_message(user + " has cleared stored values")
			storedStrikes = []
			chnl = bot.get_channel(1055967445652865130)
			tickers.append( ("VIX", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
			tickers.append( ("SPX", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
			tickers.append( ("SPY", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
		print("Finished SUDO")

	@tasks.loop(seconds=1)
	async def channelUpdate():
		global tickers, counter, auto_updater, update_timer#, IVUpdateChannel, IVUpdateChannelCounter
		if len(tickers) != 0 :
			for tck in tickers:
				fn = getOOPS(tck[0], tck[1], tck[2], tck[3])
				chnl = bot.get_channel(tck[4])
				if chnl == None : chnl = tck[5]
				if fn == "error.png": await chnl.send("Failed to get data for " + tck[0])
				else: await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			tickers.clear()
		if len(auto_updater) != 0:
			counter += 1
			if counter > update_timer :
				counter = 0
				for tck in auto_updater:
					fn = stock_price(tck[0], tck[1], tck[2], tck[3])
					chnl = bot.get_channel(tck[4])
					if chnl == None : chnl = tck[5]
					await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))

	dailyTaskTime = datetime.time(hour=13, minute=40, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
	@tasks.loop(time=dailyTaskTime)
	async def dailyTask():
		if datetime.datetime.now().weekday() > 4 : return
		chnl = bot.get_channel(1055967445652865130)
		print("Daily Task Execution")
		await chnl.send("Fethcing Morning Charts")
		storedStrikes = []
		tickers.append( ("VIX", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
		tickers.append( ("SPX", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
		tickers.append( ("SPY", 0, 40, CHART_CHANGE, 1055967445652865130, chnl) )
		logData("SPX")
		logData("SPY")

	@bot.event
	async def on_ready():
		global blnFirstTime
		if blnFirstTime :
			channelUpdate.start()
			dailyTask.start()
			blnFirstTime = False
		#print("Running it")
		
	@bot.command(name="s")
	async def get_gex(ctx, *args):
		global tickers, updateRunning
		if ctx.message.author == bot.user: return
		if len(args) == 0: return
		dte = (args[1] if (len(args) > 1) and args[1].isnumeric() else '0')
		count = (args[2] if (len(args) > 2) and args[2].isnumeric() else '40')
		tickers.append( (args[0].upper(), dte, count, getChartType(args[2]) if (len(args) == 3) else 0, ctx.message.channel.id, ctx.message.channel) )

	bot.run(BOT_TOKEN)

def drawRect(draw, x, y, w, h, color, border):
	if border in 'none': border = color
	draw.rectangle([x,y,w,h], fill=color, outline=border)   #for PIL Image

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

def getATRLevels(ticker_name):
	content = getByHistoryType( False, ticker_name )
	skip = True
	previousClose = 0.0
	lastDayClose = 0.0
	atrs = []
	for candles in content['candles']:
		if skip :
			skip = False
			previousClose = candles['close']
		else:
			high = candles['high']
			low = candles['low']
			upper = abs( high - previousClose )
			lower = abs( low - previousClose )
			both = abs( high - low )
			atrs.append( max( [upper, lower, both] ) )
			previousClose = candles['close']
	if len(atrs) < 14 : 
		print("No ATR Data")
		return 0
	atrs = atrs[len(atrs) - 14:]
	atr = sum(atrs) / len(atrs)
	FIBS = [0.236, 0.382, 0.5, 0.618, 0.786]
	
	price = previousClose
	price2 = price + atr
	price3 = price - atr
	strikes = StrikeData(ticker_name, previousClose)
	
	for i in [price, price + atr, price - atr]:
		for j in FIBS:
			strikes.addStrike(i, 15, 0, 0, 0, 0, 0, 10, 0, 0, 1, 0)
			strikes.addStrike(i + atr * j, 10, 0, 0, 0, 0, 0, j * 10, 0, 0, 1, 0)
			strikes.addStrike(i - atr * j, 10, 0, 0, 0, 0, 0, j * 10, 0, 0, 1, 0)
			
#			strikes.addStrike(price2 + atr * j, 50 - (50 * j), 0, 0, 0, 0, 0, j * 5, 0, 0, 1, 0)
#			strikes.addStrike(price2 - atr * j, 50 - (50 * j), 0, 0, 0, 0, 0, j * 5, 0, 0, 1, 0)
			
#			strikes.addStrike(price3 + atr * j, 50 - (50 * j), 0, 0, 0, 0, 0, j * 5, 0, 0, 1, 0)
#			strikes.addStrike(price3 - atr * j, 50 - (50 * j), 0, 0, 0, 0, 0, j * 5, 0, 0, 1, 0)
			
	return strikes

def getByHistoryType( totalCandles, ticker ):
	if totalCandles :
		end =  2680811140000#int( datetime.datetime.now().timestamp() * 1000 )
		start = int( (datetime.datetime.now() - datetime.timedelta(days=3)).timestamp() * 1000 )
#		start = int( datetime.datetime.now().timestamp() * 1000 )
		start = end - 140000
		url_endpoint = atr2_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker, start_date=start, end_date=end)
	else :
		url_endpoint = atr_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker)
	return json.loads(requests.get(url=url_endpoint, headers=HEADER).content)

"""   ************Unfinished pandas code***********
def getPandas(ticker_name, dte, chartType = 0):
	import pandas as pd
	import numpy as np

	content = pullData( ticker_name, dte )
	df = pd.DataFrame()
	for days in content['callExpDateMap']:
		for strikes in content['callExpDateMap'][days]:
			df = pd.concat([df, pd.DataFrame(content['callExpDateMap'][days][strikes]), pd.DataFrame(content['putExpDateMap'][days][strikes])])

	df.fillna(0, inplace = True)
#	df['Date'] = pd.to_datetime(df['Date'])
	df['putCall'] = df['putCall'].replace(['CALL'], '1')
	df['putCall'] = df['putCall'].replace(['PUT'], '-1')

	df = df.drop(columns=['symbol', 'description', 'exchangeName', 'bid', 'last', 'mark', 'bidSize', 'askSize', 'bidAskSize', 'lastSize', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'tradeDate', 'tradeTimeInLong', 'quoteTimeInLong', 'netChange', 'theoreticalOptionValue', 'theoreticalVolatility', 'optionDeliverablesList', 'expirationDate', 'expirationType', 'lastTradingDay', 'multiplier', 'settlementType', 'deliverableNote', 'isIndexOption', 'percentChange', 'markChange', 'markPercentChange', 'intrinsicValue', 'nonStandard', 'mini', 'pennyPilot', 'daysToExpiration', 'inTheMoney' ])

	df['strikePrice'] = df['strikePrice'].astype(float)
	df['volatility'] = df['volatility'].astype(float)
	df['gamma'] = df['gamma'].astype(float)
	df['openInterest'] = df['openInterest'].astype(float)
	df['putCall'] = df['putCall'].astype(float)
	df['volatility'] = df['volatility'].astype(float)

	df = df.fillna(0).replace(['NaN'], 0)

	df['GEX'] = df['gamma'] * df['openInterest'] * df['putCall']
	df['DEX'] = df['delta'] * df['openInterest'] * df['putCall']
	df['VIX'] = df['vega'] * df['volatility']

	df = df.drop(columns=['gamma', 'delta', 'vega', 'theta', 'rho'])
	df_agg = df.groupby(['StrikePrice']).sum(numeric_only=True)
	
	#df['TotalGamma'] = df.GEX / 10**9
DataFrame.Series()
def summation_func(list_of_dataframes/gex/dex/vix):

total_gex/dex/vix = list_of_dataframes/gex/dex/vix[0]

   for df in listof<whatever>[1:]:
		total_gex/dex/vix += df

return total_gex/dex/vix


	print( df.to_string() )

#	print( df[df.duplicated(['strikePrice'])] )
#	print( np.where(df['strikePrice'] == 409.0) )
	strikes = {}
	strikes['Strikes'] = '0'
	for x in df.strikePrice.unique() :
		dfSum = df[ df['strikePrice'] == x].sum()
		strikes['Strikes'] = str(x) + "," + strikes['Strikes']
		strikes['GEX', x] = dfSum['GEX']
		strikes['DEX', x] = dfSum['DEX']
		strikes['OI', x] = dfSum['openInterest']

	print( strikes )

getPandas("SPY", 0, 0)
"""
class OptionData():
	def __init__(self):
		self.Gamma, self.Delta, self.Vega, self.Theta, self.TimeValue, self.IV, self.OI, self.Bid, self.Ask, self.GEX, self.DEX, self.Dollars = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
	def addStrike(self, gamma, delta, vega, theta, timeValue, iv, oi, bid, ask):
		self.Gamma = gamma
		self.Delta = delta
		self.Vega = vega
		self.Theta = theta
		self.TimeValue = timeValue
		self.IV = iv
		self.Bid = bid
		self.Ask = ask
		self.OI += oi
		self.GEX += gamma * oi
		self.DEX += delta * oi
		self.Dollars += bid * oi * 100

class StrikeData():
	def __init__(self, ticker, price):
		self.Calls, self.Puts, self.Strikes, self.Ticker, self.Price, self.DTE, self.ClosestStrike = {}, {}, [], "", 0.0, 0, 0.0
		self.distFromPrice = 9999
		self.CallDollars, self.PutDollars = 0.0, 0.0
		self.Ticker = ticker
		self.Price = round(price, 2)
	def addStrike(self, strike, gamma, delta, vega, theta, timeValue, iv, oi, bid, ask, call, dte) :
		def chk( val ) : return 0.0 if math.isnan( float( val ) ) else float( val )
		strike, gamma, delta, vega, theta, timeValue, iv, oi, bid, ask, dte = chk(strike), chk(gamma), chk(delta), chk(vega), chk(theta), chk(timeValue), chk(iv), chk(oi), chk(bid), chk(ask), chk(dte)
		if not strike in self.Strikes :
			self.Strikes.append(strike)
			self.Calls[strike] = OptionData()
			self.Puts[strike] = OptionData()
		d = self.Calls if call else self.Puts
		d[strike].addStrike(gamma, delta, vega, theta, timeValue, iv, oi, bid, ask)
		if call :
			self.CallDollars += d[strike].Dollars
		else:  #Puts are done second, these operations only need performed once
			if dte > self.DTE : self.DTE = dte
			dist = abs(self.Price - strike) 
			if dist < self.distFromPrice : 
				self.distFromPrice = dist
				self.ClosestStrike = strike
			self.PutDollars += d[strike].Dollars

def getChange(new: StrikeData) :
	stored = next((x for x in storedStrikes if new.Ticker == x.Ticker), None)
	if stored == None :
		storedStrikes.append(new)
		return new
	#Generate differential values to draw
	changeStrikes = StrikeData(new.Ticker, new.Price)
	changeStrikes.DTE = new.DTE
	changeStrikes.ClosestStrike = new.ClosestStrike
	changeStrikes.distFromPrice = new.distFromPrice
	changeStrikes.CallDollars = new.CallDollars - stored.CallDollars
	changeStrikes.PutDollars = new.PutDollars - stored.PutDollars
	changeStrikes.Strikes = [s for s in new.Strikes for ss in stored.Strikes if s == ss] #Only add duplicates
#	changeStrikes.Strikes = [s for s, ss in zip(new.Strikes, stored.Strikes) if s == ss] #Only add duplicates
	for s in changeStrikes.Strikes:
		changeStrikes.Calls[s] = OptionData()
		changeStrikes.Calls[s].GEX = new.Calls[s].GEX - stored.Calls[s].GEX
		changeStrikes.Calls[s].DEX = new.Calls[s].DEX - stored.Calls[s].DEX
		changeStrikes.Calls[s].OI = new.Calls[s].OI - stored.Calls[s].OI
		changeStrikes.Puts[s] = OptionData()
		changeStrikes.Puts[s].GEX = new.Puts[s].GEX - stored.Puts[s].GEX
		changeStrikes.Puts[s].DEX = new.Puts[s].DEX - stored.Puts[s].DEX
		changeStrikes.Puts[s].OI = new.Puts[s].OI - stored.Puts[s].OI	
	return changeStrikes

def pullData(ticker_name, dte, count):
	ticker_name = ticker_name.upper()
#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
	today = datetime.date.today()
	if "SPX" in ticker_name: ticker_name = "$SPX.X"
	if "VIX" in ticker_name: ticker_name = "$VIX.X"
	if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours

#	print( today )

	loopAgain = True
	errorCounter = 0
	logCounter = 0
	while loopAgain:
		dateRange = today + datetime.timedelta(days=int(dte))
		url_endpoint = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count=str(count), toDate=dateRange)
		json_data = requests.get(url=url_endpoint, headers=HEADER).content
		content = json.loads(json_data)
		if 'error' in content:  #happens when oauth token expires
			refreshTokens()
			errorCounter += 1
			if errorCounter == 5: break
		elif (content['status'] in 'FAILED'):   #happens when stock has no options, or stock doesnt exist
			dte = str( int(dte) + 7)
			loopAgain = int(dte) < 37
		else:
			loopAgain = False
	if ('error' in content) or (errorCounter == 5) : content = {'status': 'FAILED'}
	return content

def getOOPS(ticker_name, dte, count, chartType = 0):
	err = 0
	try:
		if chartType == CHART_ATR : 
			atrs = getATRLevels(ticker_name)
			if atrs == 0: return "error.png"
			return drawOOPSChart( atrs, chartType )
		if chartType == CHART_IV : 
			strikes = StrikeData(ticker_name, 0.0)
			return drawOOPSChart(strikes, chartType)
		err = 1

		content = pullData( ticker_name, dte, count )
		if (content['status'] in 'FAILED'): 
			print( content )
			return "error.png" #Failed, we tried our best

		err = 2
		if chartType == CHART_JSON :
			ticker_name = ticker_name + ".json"
			with open(ticker_name, "w") as outfile:
				outfile.write(json.dumps(content, indent=4))
			return ticker_name
		err = 3

		strikesData = StrikeData(content['symbol'], content['underlyingPrice'])
		for days in reversed(content['callExpDateMap']):
			for stk in content['callExpDateMap'][days]:
				def addOption(opt, hasData) :
					oi = 0
					call = opt['putCall'] == "CALL"
					if hasData :
						oi = opt['totalVolume'] if (chartType == CHART_VOLUME) or (chartType == CHART_CHANGE) else opt['openInterest'] 
					else: call = not call
					strikesData.addStrike( strike=opt['strikePrice'], gamma=opt['gamma'], delta=opt['delta'], vega=opt['vega'], theta=opt['theta'], timeValue=opt['timeValue'], iv=opt['volatility'], oi=oi, bid=opt['bid'], ask=opt['ask'], call=call, dte=opt['daysToExpiration'] )
				err = 4
				for options in content['callExpDateMap'][days][stk]: 
					addOption( options, True )
					if (not days in content['putExpDateMap']) or (not stk in content['putExpDateMap'][days]) : addOption( options, False )
				for options in content['putExpDateMap'][days][stk]: 
					if (not days in content['callExpDateMap']) or (not stk in content['callExpDateMap'][days]) : addOption( options, False )
					addOption( options, True )

#				for i in range( len( content['callExpDateMap'][days][stk] ) ):  #i is always 0?
#					addOption(content['callExpDateMap'][days][stk][i], True)
#					if 	(stk in content['putExpDateMap'][days]) :
#						addOption(content['putExpDateMap'][days][stk][i], True)
#					else :   # Always add put data or else
#						print( "BOOM ", stk )
#						addOption(content['callExpDateMap'][days][stk][i], False)
				err = 5

			if chartType == CHART_LASTDTE : break
		if chartType == CHART_LOG : return strikesData
		if chartType == CHART_CHANGE : strikesData = getChange(strikesData)
		err = 6
		return drawOOPSChart( strikesData, chartType )
	except Exception as e:
		print( err, " ", e)  #4 list index out of range
		return "error.png"

def drawOOPSChart(strikes: StrikeData, chartType) :
	top, above, above2, upper, lower = {}, {}, {}, {}, {}
	maxTop, maxAbove, maxAbove2, maxUpper, maxLower = 1.0, 1.0, 1.0, 1.0, 1.0
	count = len(strikes.Strikes)
	zero = (0, 0)
	biggy = 0
	biggySize = 0
	strChart = CHARTS_TEXT[chartType]  #Many charts are able to display using CHART_GEX code.  store the name for later
	if chartType == CHART_CHANGE : chartType = CHART_GEX
	if chartType == CHART_LASTDTE : chartType = CHART_GEX
	if chartType == CHART_ATR : chartType = CHART_GEX  #ATR Code makes data look like GEX chart
	if chartType == CHART_VOLUME : chartType = CHART_GEX  #Already converted Volume to OI in pullData()
	if chartType == CHART_DAILYIV :
		for i in sorted(strikes.Strikes) :
			top[i] = abs(strikes.Calls[i].TimeValue) * 1000
			above[i] = abs(strikes.Calls[i].IV) * 1000
			above2[i] = abs(strikes.Calls[i].Vega) * 1000
			upper[i] = above[i] * above2[i]
			lower[i] = abs(strikes.Calls[i].Theta) * 1000
			if top[i] > maxTop : maxTop = top[i]
			if above[i] > maxAbove : maxAbove = above[i]
			if above2[i] > maxAbove2 : maxAbove2 = above2[i]
			if upper[i] > maxUpper :   maxUpper = upper[i]
			if lower[i] > maxLower :   maxLower = lower[i]
		
	if (chartType == CHART_ROTATE) or (chartType == CHART_GEX) :  #Fill local arrays with desired charting data
		for i in sorted(strikes.Strikes) :
			top[i] = strikes.Calls[i].OI + strikes.Puts[i].OI
			above[i] = strikes.Calls[i].GEX - strikes.Puts[i].GEX
			above2[i] = strikes.Calls[i].DEX + strikes.Puts[i].DEX
			upper[i] = strikes.Calls[i].GEX
			lower[i] = strikes.Puts[i].GEX
			if top[i] > maxTop : maxTop = top[i]
			if abs(above[i]) > maxAbove : maxAbove = abs(above[i])
			if abs(above2[i]) > maxAbove2 : maxAbove2 = abs(above2[i])
			if upper[i] > maxUpper : maxUpper = upper[i]
			if lower[i] > maxUpper : maxUpper = lower[i]

			tmp = lower[i] + upper[i]
			if tmp > biggySize : 
				biggySize = tmp
				biggy = i

		maxLower = maxUpper
		zero = zero_gex( above )
	if chartType == CHART_IV :
		data = loadIVLog(strikes.Ticker)
		data.pop('IVData')
		maxLower = 9999999
		for days in data:
			above[days] = data[days]['atm'] * 1000
			upper[days] = data[days]['calls'] * 1000
			lower[days] = data[days]['puts'] * 1000
			if above[days] > maxUpper : maxUpper = above[days]
			if upper[days] > maxUpper : maxUpper = upper[days]
			if lower[days] > maxUpper : maxUpper = lower[days]	

			if above[days] < maxLower : maxLower = above[days]
			if upper[days] < maxLower : maxLower = upper[days]
			if lower[days] < maxLower : maxLower = lower[days]
			
			strikes.CallDollars = data[days]['calls']
			strikes.PutDollars = data[days]['puts']
			strikes.ClosestStrike = data[days]['atm']
		for days in data:
			above[days] -= maxLower
			upper[days] -= maxLower
			lower[days] -= maxLower
		count = len(above)
		strikes.DTE = count
		if count == 0 : return "error.png"

#Draw the data
	IMG_W = ((FONT_SIZE - 3) * count) + 150
	if chartType != CHART_ROTATE : IMG_W += 100
	img = PILImg.new("RGB", (IMG_H, IMG_W), "#000") if chartType == CHART_ROTATE else PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	x = 0
	if chartType == CHART_IV :
	
		x = -5
		date = list(above.keys())[0]
		aY = above[date]
		uY = upper[date]
		lY = lower[date]
		lastX = x
		y = IMG_H - 140
		drawText(draw, x=IMG_W - 80, y=y-200-FONT_SIZE, txt=str(maxUpper / 1000), color="#CCC")
		drawRotatedPriceLine(draw, y - 200, "#FF0")
		
		drawText(draw, x=IMG_W - 80, y=y-FONT_SIZE, txt=str(maxLower / 1000), color="#CCC")
		drawRotatedPriceLine(draw, y, "#FF0")
		
		drawRotatedPriceLine(draw, y-100, "#FF0")
		drawText(draw, x=IMG_W - 80, y=y-100-FONT_SIZE, txt=str((maxLower + ((maxUpper - maxLower) / 2)) / 1000), color="#CCC")
		
		maxUpper -= maxLower

		for i in above:
			x += FONT_SIZE - 3
			drawRotatedText(img, x=x - 5, y=y + 20, txt=i, color="#77F")
			
			draw.line([lastX, y - ((aY / maxUpper) * 200), x, y - ((above[i] / maxUpper) * 200)], fill="yellow", width=1)
			aY = above[i]
			
			draw.line([lastX, y - ((uY / maxUpper) * 200), x, y - ((upper[i] / maxUpper) * 200)], fill="#7F7", width=1)
			uY = upper[i]
			
			draw.line([lastX, y - ((lY / maxUpper) * 200), x, y - ((lower[i] / maxUpper) * 200)], fill="#F77", width=1)
			lY = lower[i]
			
			lastX = x
		x = 5
	elif chartType == CHART_ROTATE :
		x = IMG_W - 15
		for strike in sorted(strikes.Strikes) :
			x -= FONT_SIZE - 3
			drawText(draw, y=x - 5, x=218, txt=str(round(strike, 2)), color="#CCC")   # .replace('.0', '')
			if (top[strike] != 0) : drawRect(draw, 0, x, ((top[strike] / maxTop) * 65), x + 12, color="#00F", border='')
			if (above[strike] != 0) : drawRect(draw, 215 - ((abs(above[strike]) / maxAbove) * 150), x, 215, x + 12, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			if (above2[strike] != 0) : drawRect(draw, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x, 215, x + 2, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			if (upper[strike] != 0) : drawRect(draw, 399 - ((upper[strike] / maxUpper) * 100), x, 399, x + 12, color="#0f0", border='')
			if (lower[strike] != 0) : drawRect(draw, 401 + ((lower[strike] / maxLower) * 100), x, 401, x + 12, color="#f00", border='')
			if strike == strikes.ClosestStrike: drawRotatedPriceLine(draw,x - 5 if strikes.Price > strikes.ClosestStrike else x + FONT_SIZE, "#FF0")
			if strike == zero[0] : drawRotatedPriceLine(draw, x + 8, "#FFF")
			if strike == zero[1] : drawRotatedPriceLine(draw, x + 8, "#FFF")
			if strike == biggy : drawRotatedPriceLine(draw, x + 8, "#330")
		x = 0
	else :
		x = -15
		for strike in sorted(strikes.Strikes) :
			x += FONT_SIZE - 3
			drawRotatedText(img, x=x - 5, y=220, txt=str(round(strike, 2)), color="#3F3")   # .replace('.0', '')
			if (top[strike] != 0) : drawRect(draw, x, 0, x + 12, ((top[strike] / maxTop) * 65), color="#00F", border='')
			if (above[strike] != 0) : drawRect(draw, x, 215 - ((abs(above[strike]) / maxAbove) * 150), x + 12, 215, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			if (above2[strike] != 0) : drawRect(draw, x, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x + 2, 215, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			if (upper[strike] != 0) : drawRect(draw, x, 399 - ((upper[strike] / maxUpper) * 100), x + 12, 399, color="#0f0", border='')
			if (lower[strike] != 0) : drawRect(draw, x, 401 + ((lower[strike] / maxLower) * 100), x + 12, 401, color="#f00", border='')
			if strike == strikes.ClosestStrike: drawPriceLine(draw, x + 10 if strikes.Price > strikes.ClosestStrike else x, "#FF0")
			if strike == zero[0] : drawPriceLine(draw, x + 5, "#FFF")
			if strike == zero[1] : drawPriceLine(draw, x + 5, "#FFF")
			if strike == biggy : drawRotatedPriceLine(draw, x + 8, "#330")
		x += 15
	drawText(draw, x=x, y=0, txt=strikes.Ticker + " " + "${:,.2f}".format(strikes.Price, 2), color="#3FF")
	drawText(draw, x=x, y=FONT_SIZE, txt=strChart + str(int(strikes.DTE)) + "-DTE", color="#3FF")
	if chartType == CHART_IV :
		drawText(draw, x=x, y=FONT_SIZE * 2, txt="Calls " + str(strikes.CallDollars) + "%", color="#0f0")
		drawText(draw, x=x, y=FONT_SIZE * 3, txt="ATM " + str(strikes.ClosestStrike) + "%", color="yellow")
		drawText(draw, x=x, y=FONT_SIZE * 4, txt="Puts " + str(strikes.PutDollars) + "%", color="#f00")
	else : 
		drawText(draw, x=x, y=FONT_SIZE * 2, txt="Calls "+"${:,.2f}".format(strikes.CallDollars), color="#0f0")
		drawText(draw, x=x, y=FONT_SIZE * 3, txt="Puts "+"${:,.2f}".format(strikes.PutDollars), color="#f00")
		drawText(draw, x=x, y=FONT_SIZE * 4, txt="Total "+"${:,.2f}".format(strikes.CallDollars-strikes.PutDollars), color="yellow")
		drawText(draw, x=x, y=FONT_SIZE * 5, txt="Zero Gamma "+"${:,.2f}".format(zero[0])+" - ${:,.2f}".format(zero[1]), color="orange")

	img.save("stock-chart.png")
	return "stock-chart.png"

def drawIVText(img, x, y, txt, color):
	text_layer = PILImg.new('L', (100, FONT_SIZE))
	dtxt = ImageDraw.Draw(text_layer)
	dtxt.text( (0, 0), txt, fill=255, font=font)
	rotated_text_layer = text_layer.rotate(270.0, expand=1)
	PILImg.Image.paste( img, rotated_text_layer, (x,y) )

def logData(ticker_name):
	fileName = ticker_name + "-IV.json"
	strikes = getOOPS(ticker_name, 0, 40, CHART_LOG)
	today = str(datetime.date.today())
	atmIV = strikes.Calls[strikes.ClosestStrike].IV
	data = loadIVLog(ticker_name)
	callIV = 0.0
	putsIV = 0.0
	for x in range(len(strikes.Strikes)) :
		if strikes.Strikes[x] == strikes.ClosestStrike : 
			callIV = strikes.Calls[strikes.Strikes[x + 5]].IV
			putsIV = strikes.Calls[strikes.Strikes[x - 5]].IV
	newData = {"atm": atmIV, "calls": callIV, "puts": putsIV}
	print( fileName, " - ", strikes.ClosestStrike, " - ", atmIV, " - ", today )
	print( newData )
	data[str(today)] = newData

	json.dump(data, open(fileName,'r+'), indent = 4)

def loadIVLog(ticker_name):
	fileName = ticker_name + "-IV.json"
	if not exists(fileName):  
		with open(fileName, "w") as outfile:  
			outfile.write('{"IVData": "SPX"}')   #File Must have contents for JSON decoder
	return json.load(open(fileName,'r+'))

def zero_gex(data):
	def add(a, b): return (b[0], a[1] + b[1])
	strikes = [] #convert data dict to the tuples list function requires
	for d in data : strikes.append( (d, data[d]) )   # list(strike, GEX)
	cumsum = list(accumulate(strikes, add)) #each elements gamma is added to the one after it
	return min(cumsum, key=lambda i: i[1])[0], max(cumsum, key=lambda i: i[1])[0]
#	if cumsum[len(strikes) // 10][1] < 0: #[en(strikes) // 10] should always have a negative gamma?
#		op = min  #assigning a variable to a function
#	else: 
#		op = max
#	result = op(cumsum, key=lambda i: i[1])[0]   # lambda returns the strike, from 2nd element in list
#	test = max(cumsum, key=lambda i: abs(i[1]))[0]   #sort by gamma, return the strike
#	print( result, test )

def fetchEvents():
	try :
		WEEKDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
		url = "https://www.marketwatch.com/economy-politics/calendar"
		print("fetching calender")
		data = requests.get(url=url)
		day = datetime.datetime.now().weekday()
		txt = data.text.split( "<tbody>" )[1].split("</tbody>")[0].split( WEEKDAY[day] )[1].split("<b>")[0].strip(', ').split('<td style="text-align: left;">')
		firstWord = txt[0].split(' ')[0]

		clean = re.compile('<.*?>')
		#return re.sub(clean, '', text)
		text = txt[0].split('</b>')[0] + '\n'
		counter = 0
		for s in txt:
			tmp = re.sub(clean, '', s).strip('\n')#.strip('S&amp;P')
			if ' am' in tmp or ' pm' in tmp: counter = 1

			if counter > 0:
				counter += 1
				xtmp = tmp.split('S&amp;P')
				text += xtmp[0]
				if len(xtmp) > 1 : text += xtmp[1]
				#if firstWord in tmp.upper() : text += '\n'
				#elif tmp != '' : text += tmp
			if counter == 3:
				counter = 0
				text += '\n'

		return text
	except :
		return "Tell Smay its broke....."



thread_discord()