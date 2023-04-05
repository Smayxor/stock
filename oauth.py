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

from datetime import date
from datetime import datetime as dt
import datetime
import time
import requests
import json
import math
import os
#import logging
import threading
import sys
#from colour import Color
import random
import csv
import urllib.parse
from urllib.parse import quote as enc
from os.path import exists
from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont
import PIL.Image as PILImg
from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands

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
atr2_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&endDate={end_date}&startDate={start_date}&needExtendedHoursData=false"

CHART_GEX = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_TIMEVALUE = 3
CHART_ROTATE = 4
CHART_JSON = 5
CHART_ATR = 6

CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "TIME VALUE ", "ROTATED ", "JSON ", "ATR+FIB "]

FONT_SIZE = 22
STR_FONT_SIZE = str(int(FONT_SIZE / 2))  #strangely font size is 2x on tkinter canvas
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic") #Place font file in same folder, or use supply path if needed in Linux

IMG_W = 1000
IMG_H = 500
IVUpdateChannel = []
IVUpdateChannelCounter = 0

#Generate a color gradient between red and green, used to rate fundamentals and look cool doing it
#red = Color("#FF0000")
#colorGradient = list(red.range_to(Color("#00FF00"),10))
#colorGradient[0] = "#FF0000"
#colorGradient[9] = "#00FF00"

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
				code = urllib.parse.unquote( self.path.split(str('code='))[1] )# urllib.parse.unquote()
				print(code)
				oauth_params['code'] = code
				oauth_params['grant_type'] = 'authorization_code'
				oauth_params['refresh_token'] = ''
				oauth_params['access_type'] = 'offline'
				oauth_params['redirect_uri'] = 'https://localhost:8080/'
				page = requests.post(url=auth_endpoint.format(api_key=MY_API_KEY), headers=SERVER_HEADER, data=oauth_params)
				print(urllib.parse.unquote(page.content))
				with open("access-token.json", "w") as outfile:
					outfile.write(urllib.parse.unquote(page.content))
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
	if exists('access-token.json'):   #Mysteriously REFRESH_TOKEN was empty *********** loadAccessTokens() should of happened?????
		init = json.load(open('access-token.json', 'rb'))
		if 'refresh_token' in init:
			REFRESH_TOKEN = init['refresh_token']
	oauth_params['grant_type'] = 'refresh_token'
	oauth_params['refresh_token'] = REFRESH_TOKEN
	oauth_params['access_type'] = ''
	oauth_params['redirect_uri'] = ''
	oauth_params['code'] = ''
	#When Refresh Token ultimately times out, this method will fail in 90 days   *******************************
	page = urllib.parse.unquote(requests.post(url="https://api.tdameritrade.com/v1/oauth2/token", headers=SERVER_HEADER, data=oauth_params).content)
	merge = "{\n  \"refresh_token\": \"" + REFRESH_TOKEN + "\", \n  \"refresh_token_expires_in\": " + str(init['refresh_token_expires_in']) + ", " + page.split("{")[1]
	with open("access-token.json", "w") as outfile:
		outfile.write(merge)
	loadAccessTokens()
refreshTokens()

#Declarations for slash commands
url = "https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands"
headers = { "Authorization": "Bot " + BOT_TOKEN}
slash_command_json = {
	"name": "gex", "type": 1, "description": "Draw a GEX/DEX chart", "options": [ { "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, { "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, { "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [{ "name": "Normal", "value": "Normal"  }, { "name": "Rotated", "value": "R" }, { "name": "Volume", "value": "V" }, { "name": "TimeValue", "value": "TV"  }, { "name": "IV", "value": "IV"  }, { "name": "JSON", "value": "JSON"  }, { "name": "ATR", "value": "ATR"  }]}   ] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "8ball", "type": 1, "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "sudo", "type": 1, "description": "Shuts off Smayxor", "options":[{ "name": "command", "description": "Super User ONLY!", "type": 3, "required": True }] }
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

gms = [enc("gm friends"), enc("good morning coffee"), enc("wake up"), enc("time to work")]
pumps = [enc("stock pump rocket moon"), enc("stock bull"), enc("pepe money rain")]
dumps = [enc("stock dump crash"), enc("bear stock")]
titties = [enc("boobs bounce breast"), enc("women motorboat boobs"), enc("asian tits")]
asses = [enc("women ass twerk poggers"), enc("women sexy butt"), enc("latina big ass")]

tickers = []
counter = 0
auto_updater = []
intents = discord.Intents.all()
updateRunning = False

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
update_timer = 300
bot = commands.Bot(command_prefix='}', intents=intents, help_command=MyNewHelp(), sync_commands=True)
def thread_discord():
	def getChartType( arg ):
		arg = arg.upper()
		if arg == 'V': return CHART_VOLUME
		elif arg == 'IV': return CHART_IV
		elif arg == 'TV': return CHART_TIMEVALUE
		elif arg == 'R': return CHART_ROTATE
		elif arg == 'JSON': return CHART_JSON
		elif arg == 'ATR': return CHART_ATR
		else: return CHART_GEX

	@bot.tree.command(name="gex", description="Draws a GEX chart")
	async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, chart: str = "GEX"):
		global tickers, updateRunning, counter, auto_updater, IVUpdateChannel, IVUpdateChannelCounter, CallATMIV, PutATMIV
		ticker = ticker.upper()
		await intr.response.send_message("Fetching " + CHARTS_TEXT[getChartType(chart)] + " chart for " + ticker + " " + str(dte) + "DTE")
		tickers.append( (ticker, dte, getChartType(chart), intr.channel.id, intr.channel) )
		if updateRunning == False :
			print("Starting queue")
			updateRunning = True
			channelUpdate.start()

	@bot.command(name="pump")
	async def command_pump(ctx, *args):
		if random.random() < 0.91 :
			await ctx.send( getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
		else:
			await ctx.send(file=discord.File(random.choice(["./pepe-money.gif", "./wojak-pump.gif"])))

	@bot.command(name="dump")
	async def command_dump(ctx, *args):
		await ctx.send( getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )

	@bot.command(name="tits")
	async def command_tits(ctx, *args):
		await ctx.send( getTenorGIF( random.choice(titties) + enc(" " + ' '.join(args)) ) )

	@bot.command(name="ass")
	async def command_ass(ctx, *args):
		await ctx.send( getTenorGIF( random.choice(asses) + enc(" " + ' '.join(args)) ) )

	@bot.command(name="gm")
	async def command_gm(ctx, *args):
		if random.random() < 0.91 :
			await ctx.send( getTenorGIF( random.choice(gms) + enc(" " + ' '.join(args)) ) )
		else:
			await ctx.send(file=discord.File('./bobo-gm-frens.gif'))

	@bot.tree.command(name="8ball", description="Answers your question?")
	async def slash_command_8ball(intr: discord.Interaction, question: str):
		future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good']
		if "?" in question: await intr.response.send_message("Question: " + question + "\rAnswer: " + random.choice(future))
		else: await intr.response.send_message("Please phrase that as a question")

	@bot.tree.command(name="sudo")
	@commands.is_owner()
	async def slash_command_sudo(intr: discord.Interaction, command: str):
		global tickers, updateRunning, counter, auto_updater, update_timer, IVUpdateChannel, IVUpdateChannelCounter, CallATMIV, PutATMIV
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
			chart = getChartType(args[3]) if (len(args) > 3) else CHART_GEX
			update_timer = int(args[4]) if (len(args) > 4) and args[4].isnumeric() else 300
			print("Appending to Auto_Updater array :", args[1], dte, chart, intr.channel.id, update_timer)
			auto_updater.append( (args[1], dte, chart, intr.channel.id, intr.channel) )
			if updateRunning == False :
				print("Starting queue")
				updateRunning = True
				channelUpdate.start()
			await intr.response.send_message(user + " started auto-update on " + args[1] + " " + str(dte) + "dte " + str(chart) + "-Chart " + str(update_timer) + " seconds" )
		elif args[0] == "STOP" :
			auto_updater.clear()
			CallATMIV = {}
			PutATMIV = {}
			IVUpdateChannel = []
			await intr.response.send_message(user + " stopped auto-updater")
		elif args[0] == "IV" :
			if not BOT_USER_FOR_KILL in message.author.name: return
			ticky = args[1].upper()
			IVUpdateChannel = (ticky, message.channel.id)
			IVUpdateChannelCounter = 300
			if updateRunning == False :
				print("Starting queue, IV Monitor")
				updateRunning = True
				channelUpdate.start()
			await intr.response.send_message(user + " started IV Chart process")
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
			print("Finished SUDO")

	@tasks.loop(seconds=1)
	async def channelUpdate():
		global tickers, counter, auto_updater, update_timer, IVUpdateChannel, IVUpdateChannelCounter
		if len(tickers) != 0 :
			for tck in tickers:
				#fn = stock_price(tck[0], tck[1], tck[2])
				fn = getOOPS(tck[0], tck[1], tck[2])
				chnl = bot.get_channel(tck[3])
				if chnl == None : chnl = tck[4]
				if fn == "error.png": await chnl.send("Failed to get data for " + tck[0])
				else: await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
				tickers.clear()
		if len(auto_updater) != 0:
			counter += 1
			if counter > update_timer :
				counter = 0
				for tck in auto_updater:
					fn = stock_price(tck[0], tck[1], tck[2])
					chnl = bot.get_channel(tck[3])
					if chnl == None : chnl = tck[4]
					await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		if len(IVUpdateChannel) != 0:
			IVUpdateChannelCounter += 1
			if IVUpdateChannelCounter > 300 :
				IVUpdateChannelCounter = 0
				print( "Looping ", IVUpdateChannel , IVUpdateChannelCounter )
				fn = stock_price(IVUpdateChannel[0], 0, CHART_IV)
				await bot.get_channel(IVUpdateChannel[1]).send(file=discord.File(open('./' + fn, 'rb'), fn))

	@bot.command(name="s")
	async def get_gex(ctx, *args):
		global tickers, updateRunning
		if ctx.message.author == bot.user: return
		if len(args) == 0: return
		dte = (args[1] if (len(args) > 1) and args[1].isnumeric() else '0')
		tickers.append( (args[0].upper(), dte, getChartType(args[2]) if (len(args) == 3) else 0, ctx.message.channel.id, ctx.message.channel) )
		if updateRunning == False :
			print("Starting queue")
			updateRunning = True
			channelUpdate.start()

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
	text_layer = PILImg.new('L', (100, FONT_SIZE))
	dtxt = ImageDraw.Draw(text_layer)
	dtxt.text( (0, 0), txt, fill=255, font=font)
	rotated_text_layer = text_layer.rotate(270.0, expand=1)
	PILImg.Image.paste( img, rotated_text_layer, (x,220) )

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
		else: #timestamp = datetime.datetime.fromtimestamp( (candles['datetime'] / 1000) + 7200  ) #print( timestamp )
			high = candles['high']
			low = candles['low']
			upper = abs( high - previousClose )
			lower = abs( low - previousClose )
			both = abs( high - low )
			atrs.append( max( [upper, lower, both] ) )
			#lastDayClose = previousClose
			previousClose = candles['close']
	atrs = atrs[len(atrs) - 14:]
	atr = sum(atrs) / len(atrs)

	#if (int(time.strftime("%H")) > 12): previousClose = lastDayClose
	lowerTrigger = previousClose - 0.236 * atr
	upperTrigger = previousClose + 0.236 * atr
	GEX = {}
	upper = round(previousClose + atr, 2)
	lower = round(previousClose - atr, 2)
	GEX[upper] = 10
	GEX[lower] = -10
	GEX[round(previousClose, 2)] = 1
	GEX[round(lowerTrigger, 2)] = -20
	GEX[round(upperTrigger, 2)] = 20
	GEX[round(previousClose - atr * 0.618, 2)] = -10
	GEX[round(previousClose + atr * 0.618, 2)] = 10
	GEX[round(lower - atr * 0.236, 2)] = -10
	GEX[round(upper + atr * 0.236, 2)] = 10
	GEX[round(lower - atr * 0.618, 2)] = -10
	GEX[round(upper + atr * 0.618, 2)] = 10
#		GEX[round(previousClose - atr * 0.382, 2)] = -10
#		GEX[round(previousClose + atr * 0.382, 2)] = 10
#		GEX[round(previousClose - atr * 0.5, 2)] = -10
#		GEX[round(previousClose + atr * 0.5, 2)] = 10
#		GEX[round(previousClose - atr * 0.786, 2)] = -10
#		GEX[round(previousClose + atr * 0.786, 2)] = 10
#		GEX[round(lower - atr * 0.382, 2)] = -10
#		GEX[round(upper + atr * 0.382, 2)] = 10
#		GEX[round(lower - atr * 0.5, 2)] = -10
#		GEX[round(upper + atr * 0.5, 2)] = 10
#		GEX[round(lower - atr * 0.786, 2)] = -10
#		GEX[round(upper + atr * 0.786, 2)] = 10
	upper = round(upper + atr, 2)
	lower = round(lower - atr, 2)
	GEX[lower] = -15
	GEX[upper] = 15
	GEX[round(previousClose - atr * 0.618, 2)] = -10
	GEX[round(previousClose + atr * 0.618, 2)] = 10
	GEX[round(lower - atr * 0.236, 2)] = -10
	GEX[round(upper + atr * 0.236, 2)] = 10
	GEX[round(lower - atr * 0.618, 2)] = -10
	GEX[round(upper + atr * 0.618, 2)] = 10
	GEX[round(lower - atr, 2)] = -5
	GEX[round(upper + atr, 2)] = 5
#		GEX[round(previousClose - atr * 0.382, 2)] = -10
#		GEX[round(previousClose + atr * 0.382, 2)] = 10
#		GEX[round(previousClose - atr * 0.5, 2)] = -10
#		GEX[round(previousClose + atr * 0.5, 2)] = 10
#		GEX[round(previousClose - atr * 0.786, 2)] = -10
#		GEX[round(previousClose + atr * 0.786, 2)] = 10
#		GEX[round(lower - atr * 0.382, 2)] = -10
#		GEX[round(upper + atr * 0.382, 2)] = 10
#		GEX[round(lower - atr * 0.5, 2)] = -10
#		GEX[round(upper + atr * 0.5, 2)] = 10
#		GEX[round(lower - atr * 0.786, 2)] = -10
#		GEX[round(upper + atr * 0.786, 2)] = 10
	return GEX

def getByHistoryType( totalCandles, ticker ):
	if totalCandles :
		end = int( datetime.datetime.now().timestamp() * 1000 )
		start = int( (datetime.datetime.now() - datetime.timedelta(days=3)).timestamp() * 1000 )
#		print( start, end, ticker )
		url_endpoint = atr2_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker, start_date=start, end_date=end)
#		print(url_endpoint)
	else :
		url_endpoint = atr_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker)
#		print(url_endpoint)
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



def pullData(ticker_name, dte):
	ticker_name = ticker_name.upper()
#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
	today = date.today()
	if "SPX" in ticker_name: ticker_name = "$SPX.X"
	if "VIX" in ticker_name: ticker_name = "$VIX.X"
	if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours

	loopAgain = True
	errorCounter = 0
	logCounter = 0
	while loopAgain:
		dateRange = today + datetime.timedelta(days=int(dte))
		url_endpoint = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', toDate=dateRange)
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

class OptionData():
	Gamma, Delta, Vega, Theta, TimeValue, IV, OI, Bid, Ask, GEX, DEX, Dollars = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
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
		self.GEX += gamma * oi  #Only need to use += for summing multiple days
		self.DEX += delta * oi
		self.Dollars += bid * oi * 100

class StrikeData():
	Calls, Puts, Strikes, Ticker, Price, DTE, ClosestStrike = {}, {}, [], "", 0.0, 0, 0.0
	distFromPrice = 9999
	CallDollars, PutDollars = 0.0, 0.0
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

def getOOPS(ticker_name, dte, chartType = 0):
	content = pullData( ticker_name, dte )
	if (content['status'] in 'FAILED'): #Failed, we tried our best
		clearScreen()
		drawText(0,0,txt="Failed to get data", color="#FF0")
		img.save("error.png")
		return "error.png"

	if chartType == CHART_JSON :
		ticker_name = ticker_name + ".json"
		with open(ticker_name, "w") as outfile:
			outfile.write(json.dumps(content, indent=4))
		return ticker_name

	strikesData = StrikeData(content['symbol'], content['underlyingPrice'])
	for days in content['callExpDateMap']:
		for stk in content['callExpDateMap'][days]:
			def addOption(option) :
				oi = options['totalVolume'] if chartType == CHART_VOLUME else options['openInterest']
				strikesData.addStrike( strike=options['strikePrice'], gamma=options['gamma'], delta=options['delta'], vega=options['vega'], theta=options['theta'], timeValue=options['timeValue'], iv=options['volatility'], oi=oi, bid=options['bid'], ask=options['ask'], call=options['putCall'] == "CALL", dte=options['daysToExpiration'] )
			for options in content['callExpDateMap'][days][stk]: addOption( options )
			for options in content['putExpDateMap'][days][stk]: addOption( options )
	return drawOOPSChart( strikesData, chartType )

def drawOOPSChart(strikes: StrikeData, chartType) :
	img = PILImg.new("RGB", (IMG_H, IMG_W), "#000") if chartType == CHART_ROTATE else PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)
	top, above, above2, upper, lower = {}, {}, {}, {}, {}
	maxTop, maxAbove, maxAbove2, maxUpper, maxLower = 1.0, 1.0, 1.0, 1.0, 1.0

	if chartType == CHART_TIMEVALUE : chartType = CHART_IV
	strChart = CHARTS_TEXT[chartType]
	if chartType == CHART_VOLUME : chartType = CHART_GEX  #Already converted Volume to OI in pullData()
	if chartType == CHART_IV :
		for i in sorted(strikes.Strikes) :
			top[i] = strikes.Calls[i].TimeValue * 100
			upper[i] = strikes.Calls[i].IV * 100
			lower[i] = strikes.Calls[i].Vega * 100
			above[i] = upper[i] * lower[i]
			above2[i] = strikes.Calls[i].Theta * 100
			if top[i] > maxTop : maxTop = top[i]
			if abs(above[i]) > maxAbove : maxAbove = abs(above[i])
			if abs(above2[i]) > maxAbove2 : maxAbove2 = abs(above2[i])
			if upper[i] > maxUpper : maxUpper = upper[i]
			if lower[i] > maxUpper : maxUpper = lower[i]
			
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
		maxLower = maxUpper

#	if chartType == CHART_ATR :
#		above[i] = getATRLevels(strikes.Ticker)
#		maxAbove = 50

	x = 0
	if chartType == CHART_ROTATE :
		x = IMG_W - 15
		for strike in sorted(strikes.Strikes) :
			x -= FONT_SIZE - 3
			drawText(draw, y=x - 5, x=218, txt=str(round(strike, 2)), color="#CCC")   # .replace('.0', '')
			drawRect(draw, 0, x, ((top[strike] / maxTop) * 65), x + 12, color="#00F", border='')

			drawRect(draw, 215 - ((abs(above[strike]) / maxAbove) * 150), x, 215, x + 12, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			drawRect(draw, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x, 215, x + 2, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			drawRect(draw, 399 - ((upper[strike] / maxUpper) * 100), x, 399, x + 12, color="#0f0", border='')
			drawRect(draw, 401 + ((lower[strike] / maxLower) * 100), x, 401, x + 12, color="#f00", border='')
			
			if strike == strikes.ClosestStrike:
				if strikes.Price > strikes.ClosestStrike : drawRotatedPriceLine(draw, x + 10, "#FF0")
				else : drawRotatedPriceLine(draw, x, "#FF0")
		x = 0
	else :
		x = -15
		for strike in sorted(strikes.Strikes) :
			x += FONT_SIZE - 3
			drawRotatedText(img, x=x - 5, y=205, txt=str(round(strike, 2)), color="#3F3")   # .replace('.0', '')
			drawRect(draw, x, 0, x + 12, ((top[strike] / maxTop) * 65), color="#00F", border='')

			drawRect(draw, x, 215 - ((abs(above[strike]) / maxAbove) * 150), x + 12, 215, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			drawRect(draw, x, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x + 2, 215, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			drawRect(draw, x, 399 - ((upper[strike] / maxUpper) * 100), x + 12, 399, color="#0f0", border='')
			drawRect(draw, x, 401 + ((lower[strike] / maxLower) * 100), x + 12, 401, color="#f00", border='')
			
			if strike == strikes.ClosestStrike:
				if strikes.Price > strikes.ClosestStrike : drawPriceLine(draw, x + 10, "#FF0")
				else : drawPriceLine(draw, x, "#FF0")
		x += 15
	drawText(draw, x=x, y=0, txt=strikes.Ticker + " $" + "${:,.2f}".format(strikes.Price, 2), color="#3FF")
	drawText(draw, x=x, y=FONT_SIZE, txt=strChart + str(int(strikes.DTE)) + "-DTE", color="#3FF")
	drawText(draw, x=x, y=FONT_SIZE * 2, txt="Calls $"+"${:,.2f}".format(strikes.CallDollars), color="#0f0")
	drawText(draw, x=x, y=FONT_SIZE * 3, txt="Puts $"+"${:,.2f}".format(strikes.PutDollars), color="#f00")
	drawText(draw, x=x, y=FONT_SIZE * 4, txt="Total $"+"${:,.2f}".format(strikes.CallDollars+strikes.PutDollars), color="yellow")

	img.save("stock-chart.png")
	return "stock-chart.png"


#*************Main "constructor" for GUI, starts thread for Server ********************
thread_discord()
