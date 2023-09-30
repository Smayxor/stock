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

#************************************************************
#Get API Key from TDA Developer Account new App,  place in file named apikey.json with this for contents-> {"API_KEY": "your-key-here"}
init = json.load(open('apikey.json'))
MY_API_KEY = init['API_KEY']
BOT_TOKEN = init['BOT_TOKEN']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
BOT_APP_ID = init['DISCORD_APP_ID']
BOT_CLIENT_ID = init['BOT_CLIENT_ID']
TENOR_API_KEY = init['TENOR_API_KEY']
UPDATE_CHANNEL = init['UPDATE_CHANNEL']    #Channel ID stored as Integer not string
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

atr_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&periodType=month&period=1&frequencyType=daily&frequency=1&needExtendedHoursData=true"

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
CHART_SKEW = 10
CHART_HEATMAP = 11

CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "DAILY IV ", "GEX ", "JSON ", "ATR+FIB ", "LAST DTE ", "LOG-DATA ", "CHANGE IN GEX ", "SKEWED GEX ", "HEAT MAP "]
storedStrikes = []
WEEKDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
FONT_SIZE = 22
STR_FONT_SIZE = str(int(FONT_SIZE / 2))  #strangely font size is 2x on tkinter canvas
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic") #Place font file in same folder, or use supply path if needed in Linux
#ascent, descent = font.getmetrics()
#text_width = font.getmask(strike).getbbox()[2]
#text_height = font.getmask(text_string).getbbox()[3] + descent
IMG_W = 1000
IMG_H = 500

guiMode = False
n = len(sys.argv)
if (n > 1) : 
	guiMode = sys.argv[1] in "gui"
	print("Running as client GUI Mode")

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

#   **********Uncomment this section to enable HTTPServer to catch Auth Token and Refresh Token from Auth Code ***********
#* This is the server for the redirect URL.  You will have to run the link at top of this file in a web browser to login to TDA Account *
#fetches new access tokens
"""def serverOAUTH():
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
	global ACCESS_TOKEN, REFRESH_TOKEN
	if exists('access-token.json'):
		init = json.load(open('access-token.json', 'rb'))
		if 'access_token' in init:
			ACCESS_TOKEN = init['access_token']
			REFRESH_TOKEN = init['refresh_token']
			HEADER['Authorization'] = "Bearer " + ACCESS_TOKEN
#loadAccessTokens()

def refreshTokens():
	global ACCESS_TOKEN, REFRESH_TOKEN, SERVER_HEADER
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
	"name": "gex", "type": 1, "description": "Draw a GEX/DEX chart", "options": [ { "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, { "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, { "name": "count", "description": "Strike Count", "type": 4, "required": False }, { "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [{ "name": "Normal", "value": "Normal"  }, { "name": "Rotated", "value": "R" }, { "name": "Volume", "value": "V" }, { "name": "LastDTE", "value": "LD"  }, { "name": "IV", "value": "IV"  }, { "name": "DailyIV", "value": "DAILYIV"  }, { "name": "JSON", "value": "JSON"  }, { "name": "SKEW", "value": "SKEW"  }, { "name": "HEATMAP", "value": "HEATMAP"  }]}   ] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "8ball", "type": 1, "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "sudo", "type": 1, "description": "Stuff you cant do on Smayxor", "options":[{ "name": "command", "description": "Super User ONLY!", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "news", "type": 1, "description": "Gets todays events", "options":[{ "name": "days", "description": "How many days", "type": 3, "required": False, "choices": [{"name": "today", "value": "TODAY"}, {"name": "week", "value": "WEEK"}, {"name": "all", "value": "ALL"}, {"name": "1", "value": "1"}, {"name": "2", "value": "2"}, {"name": "3", "value": "3"}, {"name": "4", "value": "4"}, {"name": "5", "value": "5"}] }] }
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
			await destination.send(strHelp)
			
logCounter = 0
logTimer = 300
			
tickers = []
counter = 0
auto_updater = []
updateRunning = False
update_timer = 300
blnFirstTime = True
bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyNewHelp(), sync_commands=True)
needsQueue = 0
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
		elif arg == 'SKEW': return CHART_SKEW
		elif arg == 'HEATMAP': return CHART_HEATMAP
		else: return CHART_GEX

	@bot.tree.command(name="gex", description="Draws a GEX chart")
	async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, count: int = 40, chart: str = "R"):
		global tickers, updateRunning, needsQueue
		await intr.response.defer(thinking=True)
		ticker = ticker.upper()
		if count < 2 : count = 2
		
		if needsQueue == 0:
			needsQueue = 1
			fn = getOOPS(ticker, dte, count, getChartType(chart))
			if fn == "error.png": await intr.followup.send("Failed to get data")
			else:
				try: await intr.followup.send(file=discord.File(open('./' + fn, 'rb'), fn))
				except: await intr.followup.send("No image permissions")
			needsQueue = 0
		else:
			await intr.followup.send("Fetching " + CHARTS_TEXT[getChartType(chart)] + " chart for " + ticker + " " + str(dte) + "DTE")
			tickers.append( (ticker, dte, count, getChartType(chart), intr.channel.id, intr.channel) )

	@bot.command(name="pump")
	async def command_pump(ctx, *args): await ctx.send( getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
	@bot.command(name="dump")
	async def command_dump(ctx, *args): await ctx.send( getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )
	@bot.command(name="tits")
	async def command_tits(ctx, *args): await ctx.send( getTenorGIF( random.choice(titties) if len( args) == 0 else enc(' '.join(args)) ) )
	@bot.command(name="ass")
	async def command_ass(ctx, *args): await ctx.send( getTenorGIF( random.choice(asses) if len( args) == 0 else enc(' '.join(args)) ) )
	@bot.command(name="gm")
	async def command_gm(ctx, *args): await ctx.send( getTenorGIF( random.choice(gms) if len( args) == 0 else enc(' '.join(args)) ) )
	
	@bot.tree.command(name="8ball", description="Answers your question?")
	async def slash_command_8ball(intr: discord.Interaction, question: str):
		future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good', 'You should ask Siri, that slut.', 'I rolled a dice to answer you, and it said the answer is C.', 'Follow your heart, I wouldn\'t trust your mind though.', 'I don\'t know and I don\'t care.', 'Did you ask ChatGPT?', 'Just google it.']
		#if "?" in question: await intr.response.send_message("Question: " + question + "\rAnswer: " + random.choice(future))
		#else: await intr.response.send_message("Please phrase that as a question")
		if "?" in question:
			response = "Question: " + question + "\rAnswer: " + random.choice(future)
		else:
			response = "Please phrase that as a question"
		await intr.response.send_message(response)

	def buildNews(days):
		today = datetime.datetime.now().weekday()
		if today > 4 : today = 0
		day = 0
		if days.isnumeric() : day = today + int(days) - 1
		elif days == "TODAY" : day = today
		elif days == "WEEK" : day = -1
		elif days == "ALL" : day = -2
		
		events = fetchNews()
		txt1 = ''
		txt2 = ''
		blnFirst = True
		for j in range(len(events) - 0):
			if day != -2:
				if day == -1:
					if j > 4: continue
				elif j < today or (j > day): continue
			tmp = events[j].toString()
			if (blnFirst == True) and (len(tmp) + len(txt1) > 1999) : blnFirst = False
			if blnFirst : txt1 += tmp
			else: txt2 += tmp
		return (txt1, txt2)
		"""
		events = fetchEvents()
		finalMessage = ""
		for j in range(len(events) - 1):
			if day != -2:
				if day == -1:
					if j > 4: continue
				elif j < today or (j > day): continue
			lines = events[j].split('\n')
#			emby = discord.Embed(title=lines[0], color=0x00ff00)
#			for i in range( len( lines ) - 1 ):
				#if i == 0: continue
#				tmp = lines[i].split('^')
#				if len(tmp) > 1:
#					emby.add_field(name=tmp[0], value=tmp[1], inline=False)
#			await chnl.send(embed=emby)
			txt = ''
			for l in lines:
				txt = txt + l + '\n'
			finalMessage += txt
		
		finalMessage = finalMessage.replace("\n\n", "\n")	
		finalMessage = finalMessage.replace("\n```\n", "```\n")	
		nextMessage = ""
		
		if len(finalMessage) > 2000: 
			txt = finalMessage.split("\n")
			finalMessage = ""
			
			for i in range(len(txt)):
				if finalMessage == "" : 
					finalMessage = txt[i]
				elif len(finalMessage) + len(txt[i]) < 1998 :
					finalMessage = finalMessage + "\n" + txt[i]
				else:
					if nextMessage == "": nextMessage = txt[i]
					else: nextMessage = nextMessage + "\n" + txt[i]
		return (finalMessage, nextMessage)	
		"""
	@bot.tree.command(name="news")
	async def slash_command_news(intr: discord.Interaction, days: str = "TODAY"):	
		await intr.response.defer(thinking=True)

		finalMessage, nextMessage = buildNews(days)
		chnl = bot.get_channel(intr.channel.id)
		try: 
			#await intr.response.send_message( finalMessage )
			await intr.followup.send( finalMessage )
		except Exception as e: 
			try: await chnl.send( finalMessage )
			except Exception as er: print("News BOOM", er)
		if len(nextMessage) != 0:
			
			try: await chnl.send( nextMessage )	
			except Exception as e: print("News 2 BOOM", e)

	@bot.tree.command(name="sudo")
	@commands.is_owner()
	async def slash_command_sudo(intr: discord.Interaction, command: str):
		global tickers, updateRunning, auto_updater, update_timer
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
			clearStoredStrikes()
		print("Finished SUDO")

	def clearStoredStrikes():
		global storedStrikes
		storedStrikes = []

	@tasks.loop(seconds=1)
	async def channelUpdate():
		global tickers, counter, auto_updater, update_timer, logCounter, logTimer, needsQueue
		needsQueue = 0
		if len(tickers) != 0 :
			for tck in tickers:
				fn = getOOPS(tck[0], tck[1], tck[2], tck[3])
				chnl = bot.get_channel(tck[4])
				if chnl == None : chnl = tck[5]
				if fn == "error.png": await chnl.send("Failed to get data for " + tck[0])
				else: 
					try: await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
					except: await chnl.send("No image permissions")
			tickers.clear()
		if len(auto_updater) != 0:
			counter += 1
			if counter > update_timer :
				counter = 0
				for tck in auto_updater:
					fn = getOOPS(tck[0], tck[1], tck[2], tck[3])
					chnl = bot.get_channel(tck[4])
					if chnl == None : chnl = tck[5]
					try: await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
					except: await chnl.send("No image permissions")
#		logTimer += 1
#		if logTimer > 60:
#			logTimer = 0
#			log = " ./logs/" + str(logCounter) + "log.json"
#			fn = "./" + getOOPS("SPX", 0, 40, CHART_JSON)
#			os.popen('cp ' + fn + log) 
#			logCounter += 1	

	dailyTaskTime = datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
#	dailyTaskTime = datetime.time(hour=9, minute=53, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
	@tasks.loop(time=dailyTaskTime)
	async def dailyTask():
		global tickers
		chnl = bot.get_channel(UPDATE_CHANNEL)
		if datetime.datetime.now().weekday() > 4 : 
			await chnl.send( buildNews("WEEK")[0] )
			return
		print("Daily Task Execution")
		await chnl.send("Fethcing Morning Charts")
		await chnl.send( buildNews("TODAY")[0] )
		clearStoredStrikes()
		#tickers.append( ("SPX", 0, 40, CHART_JSON, UPDATE_CHANNEL, chnl) )
		tickers.append( ("SPX", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		#tickers.append( ("SPY", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		#
		#logData("SPY")

	dailyTaskTime2 = datetime.time(hour=13, minute=31, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
	@tasks.loop(time=dailyTaskTime2)
	async def dailyTask2():
		global tickers
		if datetime.datetime.now().weekday() > 4 : return
		chnl = bot.get_channel(UPDATE_CHANNEL)
		print("Daily Task Execution 2")
		await chnl.send("Fethcing Morning Charts")
		#tickers.append( ("VIX", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		tickers.append( ("SPX", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		tickers.append( ("SPX", 0, 40, CHART_ROTATE, "1156977360881586177", chnl) )
		#tickers.append( ("SPX", 0, 40, CHART_JSON, UPDATE_CHANNEL, chnl) )
		#logData("SPX")
		logData("SPX", 40)


	@bot.event
	async def on_ready():
		global blnFirstTime
		if blnFirstTime :
			channelUpdate.start()
			dailyTask.start()
			dailyTask2.start()
			blnFirstTime = False
		
	@bot.command(name="s")
	async def get_gex(ctx, *args):
		global tickers, updateRunning
		"""if ctx.message.author == bot.user: return
		if len(args) == 0: return
		dte = (args[1] if (len(args) > 1) and args[1].isnumeric() else '0')
		count = (args[2] if (len(args) > 2) and args[2].isnumeric() else '40')
		tickers.append( (args[0].upper(), dte, count, getChartType(args[2]) if (len(args) == 3) else 0, ctx.message.channel.id, ctx.message.channel) )
		"""
		clearStoredStrikes()
		chnl = bot.get_channel(UPDATE_CHANNEL)
		await chnl.send("Fethcing Morning Charts")
		tickers.append( ("SPX", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		tickers.append( ("SPY", 0, 40, CHART_ROTATE, UPDATE_CHANNEL, chnl) )
		
	@bot.command(name="leaveg")
	@commands.is_owner()
	async def leaveg(ctx, *, guild_name):
		user = str(intr.user)
		if BOT_USER_FOR_KILL != user:
			await intr.response.send_message(user + " you can't kill meme!")
			return
		guild = discord.utils.get(bot.guilds, name=guild_name) # Get the guild by name
		if guild is None:
			print("No guild with that name found.") # No guild found
			return
		await guild.leave() # Guild found
		await ctx.send(f"I left: {guild.name}!")
	
	@bot.command(name="news")
	async def news(ctx):
		#chnl = bot.get_channel(UPDATE_CHANNEL)
		await ctx.send( buildNews("WEEK")[0] )
	
	bot.run(BOT_TOKEN)

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

def isThirdFriday(d):    return d.weekday() == 4 and 15 <= d.day <= 21
"""
def fetchEvents():
	COLUMN = ['time', 'event', '\t ', 'Actual: ', 'Forecast: ', 'Prev: ', '', '', '', '', '', '']
	url = "https://www.marketwatch.com/economy-politics/calendar"
	try :
		data = requests.get(url=url)
		text = ""
		tables = data.text.split( "<tbody>" )
		txt = tables[1].split("</tbody>")[0] + tables[2].split("</tbody>")[0]
		txt = txt.replace('\t', ' ').replace('</tr>','').replace('S&amp;P', '').replace(' am', ' am#').replace(' pm', ' pm#').replace('<b>', '@**').replace('</a>', '').split('<tr>')
		
		for s in txt:
			s = s.replace('<td style="text-align: left;">', '').replace("&quot;", ":").replace('\n', '').replace('</a>', '').replace('</b>', '**END*').split('</td>')
			counter = 0
			largestSize = 0
			for t in s:
				#print("A")
				try: 
					if ('FRIDAY' in t) and (15 <= int(t.split(' ')[2].split('**')[0]) <= 21) : t = t.replace('FRIDAY', 'MOPEX - FRIDAY')
				except: pass
				#print("B")
				if '<a href=' in t:
					t = t.split('<a href=')[0] + t.split('">')[1]  #****  Use masked link  [text](url)
				#print("C")
				if counter > 1 and counter < 6 and len(t) > 1:	
					t = " " + COLUMN[counter] + t + " "
				#print("D")
				counter += 1
				if counter == 1 :
					ind = t.find('m#')
					t = t.replace('m#', 'm  ')
					if ind == 6: t = t[0:5] + ' ' + t[5:]
				#print("E")
				while (counter == 2) and (len(t) < 40): t = t + ' '
				#while (counter == 4) and (len(text) < 56): text = text + ' '
				
				#print("F")
				if counter == 2 and t[0] == ' ' : t = t + ' '
				text = text + t.lstrip()
				#print("G")
				
			text = text + "\n"
			
		text = text.split('@')
		del text[0]
		for i in range(len(text) - 1) :
			text[i] = text[i].replace('END*\n', '\n```fix\n') + '\n```'
		text.append('')
		return text
	except Exception as e:
		print( e )
		return (url, '')
"""


lastNewsDay = -1
todaysNews = None
class NewsData():
	def __init__(self, day):
		self.Day = day
		self.Events = []
	def addEvent(self, txt):
		if '<a href=' in txt:
			txt = txt.replace('</a>', '')
			txt = txt.split('<a href=')[0] + txt.split('">')[1]
		self.Events.append( txt )
	def toString(self):
		text = '**' + self.Day + '**```fix'
		for e in self.Events:
			if len( e ) > 0 : text += '\n' + e
		return text + '```'
def fetchNews():
	global lastNewsDay, todaysNews
	today = datetime.date.today()
	if lastNewsDay == today : return todaysNews
	lastNewsDay = today
	
	COLUMN = ['', ' ', '\t ', ' Actual: ', ' Forecast: ', ' Prev: ', '', '', '', '', '', '']
	url = "https://www.marketwatch.com/economy-politics/calendar"
	news = []
	try :
		data = requests.get(url=url)
		text = ""
		tables = data.text.split( "<tbody>" )
		txt = tables[1].split("</tbody>")[0] + tables[2].split("</tbody>")[0]
		txt = txt.replace('<b>', '', 1).replace('<tr>','').replace('S&amp;P', '').replace('<td style="text-align: left;">', '').replace('\r', '').replace('\n', '').split('<b>')
		for t in txt:
			t = t.split('</tr>', 1)
			day = t[0].replace('</td>', '').replace('</b>', '').replace('. ', '.').replace('.', ' ')
			if ('FRIDAY' in day) and (15 <= int(day.split(' ')[2]) <= 21) : day = day.replace('FRIDAY', 'MOPEX - FRIDAY')
			newsD = NewsData( day )
			for r in t[1].split('</tr>'):
				event = ""
				counter = 0
				for td in r.split('</td>'):
					if counter == 0:
						if len(td) == 7 : td += " "
						event = td
					else:
						while (counter == 1) and (len(td) < 40): td = td + ' '	
						if len(td) > 0: event += COLUMN[counter] + td
					counter += 1
				newsD.addEvent( event )
			news.append( newsD )
	except:
		news.append( NewsData() )
	todaysNews = news
	return news

def fetchEarnings():
	url = "https://www.earningswhispers.com/calendar?sb=p&d=0&t=all&v=t"
	data = requests.get(url=url)
	text = ""
	text = data.text.split('<div id="fb-root">')[1].replace('<script', '').replace('\r\n', '').split('<div class="ticker" onclick="javascript:location.href=\'epsdetails/')
	tmp = []
	for x in text:
		x = x.split('>')[1].split('</div')[0]
		if ' ' not in x : tmp.append( x )
		
	return tmp
#fetchEarnings()

FIBS = [0.236, 0.382, 0.5, 0.618, 0.786]
def getATRLevels(ticker_name):
	ticker_name = ticker_name.upper()
	if ticker_name == "SPX" : ticker_name = "$SPX.X"
	if ticker_name == "XSP" : ticker_name = "$XSP.X"
	content = getByHistoryType( False, ticker_name )
	previousClose = 0.0
	lastCandle = len(content['candles']) - 1
	x = lastCandle
	atr = 0
	while x > lastCandle - 14:
		candles = content['candles'][x]
		#print( candles )
		x -= 1
		previousClose = content['candles'][x]['close']
		high = candles['high']
		low = candles['low']
		upper = abs( high - previousClose )
		lower = abs( low - previousClose )
		both = abs( high - low )
		atr += max( [upper, lower, both] )
	previousClose = content['candles'][lastCandle]['close']
	atr = atr / 14
	#previousClose = 4274.52
	print(previousClose, atr)
	
	result = []
	result.append((0, previousClose - atr))
	result.append((0, previousClose - atr * FIBS[4]))
	result.append((0, previousClose - atr * FIBS[3]))
	result.append((0, previousClose - atr * FIBS[2]))
	result.append((0, previousClose - atr * FIBS[1]))
	result.append((0, previousClose - atr * FIBS[0]))
	result.append((0, previousClose))
	result.append((0, previousClose + atr * FIBS[0]))
	result.append((0, previousClose + atr * FIBS[1]))
	result.append((0, previousClose + atr * FIBS[2]))
	result.append((0, previousClose + atr * FIBS[3]))
	result.append((0, previousClose + atr * FIBS[4]))
	result.append((0, previousClose + atr))
#	print( atr, previousClose )
	return result

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
	def __init__(self, ticker, price, date):
		self.TotalGEX, self.TotalOI, self.Calls, self.Puts, self.Strikes, self.Ticker, self.Price, self.DTE, self.ClosestStrike = {}, {}, {}, {}, [], "", 0.0, 0, 0.0
		self.distFromPrice = 9999
		self.CallDollars, self.PutDollars = 0.0, 0.0
		self.Ticker = ticker
		self.Price = round(price, 2)
		self.Date = date
	def addStrike(self, strike, gamma, delta, vega, theta, timeValue, iv, oi, bid, ask, call, dte) :
		def chk( val ) : return 0.0 if math.isnan( float( val ) ) or (val == -999.0) else float( val )
		strike, gamma, delta, vega, theta, timeValue, iv, oi, bid, ask, dte = chk(strike), abs(chk(gamma)), chk(delta), chk(vega), chk(theta), chk(timeValue), chk(iv), chk(oi), chk(bid), chk(ask), chk(dte)
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
			#dist = self.Price // 1
			self.PutDollars += d[strike].Dollars

def getChange(new: StrikeData) :
	stored = next((x for x in storedStrikes if new.Ticker == x.Ticker), None)
	if stored == None :
		storedStrikes.append(new)
		return new
	#Generate differential values to draw
	changeStrikes = StrikeData(new.Ticker, new.Price, '')
	changeStrikes.DTE = new.DTE
	changeStrikes.ClosestStrike = new.ClosestStrike
	changeStrikes.distFromPrice = new.distFromPrice
	changeStrikes.CallDollars = new.CallDollars - stored.CallDollars
	changeStrikes.PutDollars = new.PutDollars - stored.PutDollars
	changeStrikes.Strikes = [s for s in new.Strikes for ss in stored.Strikes if s == ss] #Only add strikes that exist in both lists
	for s in changeStrikes.Strikes:
		changeStrikes.Calls[s] = OptionData()
		changeStrikes.Calls[s].GEX = abs(new.Calls[s].GEX - stored.Calls[s].GEX)
		changeStrikes.Calls[s].DEX = abs(new.Calls[s].DEX - stored.Calls[s].DEX)
		changeStrikes.Calls[s].OI = abs(new.Calls[s].OI - stored.Calls[s].OI)
		changeStrikes.Puts[s] = OptionData()
		changeStrikes.Puts[s].GEX = abs(new.Puts[s].GEX - stored.Puts[s].GEX)
		changeStrikes.Puts[s].DEX = abs(new.Puts[s].DEX - stored.Puts[s].DEX)
		changeStrikes.Puts[s].OI = abs(new.Puts[s].OI - stored.Puts[s].OI)
	return changeStrikes

def pullData(ticker_name, dte, count):
	ticker_name = ticker_name.upper()
#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
	today = datetime.date.today()
	if "SPX" in ticker_name: ticker_name = "$SPX.X"
	if "VIX" in ticker_name: ticker_name = "$VIX.X"
	if "XSP" in ticker_name: ticker_name = "$XSP.X"
	if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours
	loopAgain = True
	errorCounter = 0
	logCounter = 0
	while loopAgain:
		dateRange = today + datetime.timedelta(days=int(dte))
		url_endpoint = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count=str(count), toDate=dateRange)
		json_data = requests.get(url=url_endpoint, headers=HEADER).content
		content = json.loads(json_data)
		#print(content)
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
			strikes = StrikeData(ticker_name, 0.0, '')
			return drawOOPSChart(strikes, chartType)
		err = 1
#		if chartType == CHART_HEATMAP : 
#			dte = 7
#			count = 20
		content = pullData( ticker_name, dte, count )
		if (content['status'] in 'FAILED'): 
			#print( content )
			return "error.png" #Failed, we tried our best

		err = 2
		if chartType == CHART_JSON :
			ticker_name = ticker_name + ".json"
			with open(ticker_name, "w") as outfile:
				outfile.write(json.dumps(content, indent=4))
			return ticker_name
		err = 3

		blank = {'strikePrice': '', 'gamma': '0', 'delta': '0', 'vega': '0', 'theta': '0', 'timeValue': '0', 'volatility': '0', 'openInterest': '0', 'bid': '0', 'ask': '0', 'putCall': '', 'daysToExpiration': '0'}
		
		sdIndex = 0
		strikesData = []
		#Days is reversed in for loop for the LAST_DTE chartType
		for days in reversed(content['callExpDateMap']):
			if chartType == CHART_HEATMAP:	strikesData.append( StrikeData(content['symbol'], content['underlyingPrice'], days) )
			elif len(strikesData) == 0 : strikesData.append( StrikeData(content['symbol'], content['underlyingPrice'], days) )
			
			for stk in content['callExpDateMap'][days]:
				def addOption(opt, hasData) :
					oi = 0
					call = opt['putCall'] == "CALL"
					if hasData :
						oi = opt['totalVolume'] if (chartType == CHART_VOLUME) or (chartType == CHART_CHANGE) else opt['openInterest'] 
					else: call = not call
					strikesData[sdIndex].addStrike( strike=opt['strikePrice'], gamma=opt['gamma'], delta=opt['delta'], vega=opt['vega'], theta=opt['theta'], timeValue=opt['timeValue'], iv=opt['volatility'], oi=oi, bid=opt['bid'], ask=opt['ask'], call=call, dte=opt['daysToExpiration'] )
				err = 4

				for i in range( len( content['callExpDateMap'][days][stk] ) ):
					try: call = content['callExpDateMap'][days][stk][i]
					except: 
						call = blank
						blank['strikePrice'] = stk
						blank['callPut'] = 'CALL'
					addOption( call, True )
					try: put = content['putExpDateMap'][days][stk][i]
					except: 
						put = blank
						blank['strikePrice'] = stk
						blank['callPut'] = 'PUT'
					addOption( put, True )
#						strikesData.addStrike( strike=stk, gamma=0, delta=0, vega=0, theta=0, timeValue=0, iv=0, oi=0, bid=0, ask=0, call=-1, dte=options['daysToExpiration'] )
				err = 5
			if chartType == CHART_HEATMAP : sdIndex += 1
			if chartType == CHART_LASTDTE : break
		if chartType == CHART_LOG : return strikesData[sdIndex]
		if chartType == CHART_CHANGE : strikesData[sdIndex] = getChange(strikesData[sdIndex])
		err = 6
		if chartType == CHART_HEATMAP : return drawHeatMap( strikesData )
		return drawOOPSChart( strikesData[sdIndex], chartType )
	except Exception as e:
		print( err, " ", str(e))
		return "error.png"

tmp = ['4', '5', '5', '6', '6', '7', '7', '7', '8', '8', '8', '9', '9', '9', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D', 'E', 'E', 'E', 'E', 'E', 'F', 'F', 'F', 'F', 'F', 'F', 'F']
LETTER = [ f'#{l}00' for l in reversed(tmp)] + ['#000'] + [ f'#0{l}0' for l in tmp]
MIDDLE_LETTER = len(tmp)
del tmp
def getColorGradient(maxVal, val):	return LETTER[int((val / maxVal) * MIDDLE_LETTER) + MIDDLE_LETTER]
def loadOldDTE(ticker):
	if "SPX" not in ticker : return []
	today = str(datetime.date.today()).split(":")[0]
	fileName = "SPX-oldDTE.json" #ticker + ".json" 
#	if not exists(fileName):  
#		with open(fileName, "w") as outfile:  
#			outfile.write('{"IVData": "SPX"}')   #File Must have contents for JSON decoder
	result = []
	try:
		data = json.load(open(fileName,'r'))
		for day in data:
			tmp = StrikeData(ticker, 0.0, '')
			if today == day : continue
			tmp.Date = day
			for strikes in data[day]:
				#print( strikes, ' ', data[day][strikes] )
				fltStrikes = float(strikes)
				tmp.Strikes.append(fltStrikes)
				tmp.Calls[fltStrikes] = OptionData()
				tmp.Puts[fltStrikes] = OptionData()
				tmp.Calls[fltStrikes].OI = data[day][strikes]['CallOI']
				tmp.Puts[fltStrikes].OI = data[day][strikes]['PutOI']
				tmp.Calls[fltStrikes].GEX = data[day][strikes]['CallGEX']
				tmp.Puts[fltStrikes].GEX = data[day][strikes]['PutGEX']
			result.append( tmp )
	except Exception as er: 
		print("Load Data BOOM", er)
		print('Check file contents ', fileName)
	return result

def logData(ticker_name, count):
	""" CHANGE to store -1dte """
	strikes = getOOPS(ticker_name, 0, 40, CHART_LOG)
	today = str(datetime.date.today()).split(":")[0]
	fileName = ticker_name + "-oldDTE.json"  #   today + "_" + 

	data = {}
	for x in strikes.Strikes :
		#if int(x.split(":")[1]) > -5 :
		data[x] = { "CallOI": strikes.Calls[x].OI, "PutOI": strikes.Puts[x].OI, "CallGEX": strikes.Calls[x].GEX, "PutGEX": strikes.Puts[x].GEX }
		#else: print( "Purging old DTE ", x )

	datedData = {today: data}

	try:
		with open(fileName, 'r') as f:
			oldData = json.load(f)
		datedData.update(oldData)
	except:
		print('logData: Check oldData file contents ', fileName)
	
	with open(fileName,'w') as f: 
		json.dump(datedData, f)

def drawHeatMap(strikes: []):
	def alignValue(val): return f'{int(val):,d}'.rjust(8)

	strikes = loadOldDTE(strikes[0].Ticker) + strikes
	strikes = sorted(strikes, key=lambda x: x.Date.split(":")[0])
	#print( [f'{d.Date}' for d in strikes] )
	
	count = len(strikes)
	lStrike = []
	dayZeroG = {}
	maxTotalGEX = 0
	for day in strikes : #Build a unique list of all strikes
		calcZeroG = {}	
		for i in day.Strikes :
			if not i in lStrike : 
				lStrike.append(i)
			day.TotalGEX[i] = day.Calls[i].GEX - day.Puts[i].GEX
			day.TotalOI[i] = day.Calls[i].OI + day.Puts[i].OI
			calcZeroG[i] = day.TotalGEX[i]
			if abs(day.TotalGEX[i]) > maxTotalGEX : maxTotalGEX = abs(day.TotalGEX[i])

		dayZeroG[day.Date] = zero_gex( calcZeroG, day.ClosestStrike ) if len( calcZeroG ) > 1 else 0.0
	#print(lStrike)
	lStrike.sort()

	if maxTotalGEX == 0.0 : return "error.png"	
	
	IMG_W = (len(strikes) + 1) * 80
	IMG_H = ((len(lStrike) + 2) * (FONT_SIZE + 2)) + 10
	img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
	draw = ImageDraw.Draw(img)		
	y = IMG_H - FONT_SIZE - 10
	for i in lStrike :
		x = 0
		y -= FONT_SIZE + 2
		
		for day in strikes :	
			x += 80
			zeroGStrike = dayZeroG[day.Date]
			if i in day.Strikes:
				color = 'yellow' if i == zeroGStrike else getColorGradient(maxTotalGEX, day.TotalGEX[i])
				drawRect(draw, x, y, x + 80, y + FONT_SIZE, color=color, border='')	
				
				val = alignValue(day.TotalOI[i])
				"""if (day.Date != strikes[0].Date) and (i in strikes[0].Strikes) :
					val = f'{alignValue( (day.TotalOI[i] / strikes[0].TotalOI[i]) * 100 )}%' 
					#val = f'    { int((day.TotalOI[i] / strikes[0].TotalOI[i]) * 100) }%'
				else : 
					val = alignValue(day.TotalOI[i])
				"""
				drawText(draw, x=x, y=y, txt=val, color="#000" if i == zeroGStrike else "#FF7")	
	
	y2 = y - (FONT_SIZE + 2)
	
	y = IMG_H - FONT_SIZE - 10
	for j in lStrike :
		draw.line([0, y, IMG_W, y], fill="white", width=1)
		y -= FONT_SIZE
		drawText(draw, x=0, y=y, txt=str(j), color="#77f")
		y -= 2
	x = 0
	y = IMG_H - FONT_SIZE - 10
	for day in strikes :
		x += 80
		strDay = datetime.datetime.strptime(day.Date.split(':')[0], '%Y-%m-%d').date().strftime("%m-%d")
		drawText(draw, x=x, y=y, txt="  " + strDay, color="#CCC")
		draw.line([x, y2, x, IMG_H], fill="white", width=1)
	
	drawRect(draw, 0, 0, IMG_W-2, FONT_SIZE+1, color="#000", border="#CCF")
	drawText(draw, x=0, y=0, txt=strikes[0].Ticker + " Options Heatmap", color="#0ff")

	img.save("stock-chart.png")
	return "stock-chart.png"
	
"""
	So say we have the 5dte gex and we wanna compare it to 3 days ago. That would mean it was 8dte at the time. You basically go back and check what the 8dte gex was. Then you'd wanna take the difference in terms of percentages. So you'd wanna do the 5dte gex, divided by the 8dte gex from the stored data.
That should give you a series/dataframe of the difference (in percentage). Then you'd wanna do 1 - that entire series/dataframe.
That should give you a negative number if it went down. If it went up, that should give you a positive number smaller than 1 (unless the GEX spiked up more than 100%)
That's the percentage change basically:

1 - <entire_series/dataframe>
And the entire_series/dataframe is this:

df_5dte / df_8dte_3daysago
"""
	
	
	
def drawOOPSChart(strikes: StrikeData, chartType) :
	top, above, above2, upper, lower = {}, {}, {}, {}, {}
	maxTop, maxAbove, maxAbove2, maxUpper, maxLower = 1.0, 1.0, 1.0, 1.0, 1.0
	count = len(strikes.Strikes)
	zero = 0
	zeroD = 0
	biggy = 0
	biggySize = 0
	maxPain = 0
	keyLevels = []
	
	strChart = CHARTS_TEXT[chartType]  #Many charts are able to display using CHART_GEX code.  store the name for later
	if chartType == CHART_CHANGE : chartType = CHART_ROTATE
	if chartType == CHART_LASTDTE : chartType = CHART_ROTATE
	if chartType == CHART_ATR : chartType = CHART_ROTATE  #ATR Code makes data look like GEX chart
	if chartType == CHART_VOLUME : chartType = CHART_ROTATE  #Already converted Volume to OI in pullData()
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

	if chartType == CHART_SKEW :
		chartType = CHART_ROTATE
		
	if (chartType == CHART_ROTATE) or (chartType == CHART_GEX):  #Fill local arrays with desired charting data
		maxP = {}
		maxPain = next(iter(strikes.Strikes))
		maxP[maxPain] = 0

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
			#calc max pain
			calls = 0
			puts = 0
			for j in strikes.Strikes :
				if i > j : calls += abs(j - i) * strikes.Calls[j].OI
				if j > i : puts += abs(j - i) * strikes.Puts[j].OI
			maxP[i] = calls + puts
			if maxP[i] < maxP[maxPain] : maxPain = i
		maxLower = maxUpper
		zero = zero_gex( above, strikes.ClosestStrike )
		zeroD = zero_gex( above2, strikes.ClosestStrike )

		largeOI = maxTop * 0.77
		largeGEX = maxAbove * 0.87
		largeCall = maxUpper * 0.8
		largePut = maxLower * 0.8
		for i in sorted(strikes.Strikes) :
			if (top[i] > largeOI) or (above[i] > largeGEX) or (upper[i] > largeCall) or (lower[i] > largePut): keyLevels.append(i)
		keyLevels.append(zero)
		keyLevels.append(maxPain)
		
		atrs = getATRLevels(strikes.Ticker)
		for i in range(len(atrs)):
			closestStrike = 0
			distToClosest = 99999
			for s in strikes.Strikes:
				tmpDist = abs(atrs[i][1] - s)
				if distToClosest > tmpDist:
					distToClosest = tmpDist
					closestStrike = s
			atrs[i] = (closestStrike, atrs[i][1])
			keyLevels.append(atrs[i][0])
	
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
	IMG_H = 500
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
			strikeColor = "#CCC"
			if strike == maxPain : strikeColor = "#F00"
			if strike == zero : strikeColor = "orange"
			if strike == zeroD : strikeColor = "#0FF"
			strikeText = str(round(strike, 2))
			for i in range(len(atrs)):
				if atrs[i][0] == strike: 
					strikeText = str(round(atrs[i][1], 1))
			drawText(draw, y=x - 5, x=218, txt=strikeText, color=strikeColor)   # .replace('.0', '')
			if (top[strike] != 0) : drawRect(draw, 0, x, ((top[strike] / maxTop) * 65), x + 12, color="#00F", border='')
			if (above[strike] != 0) : drawRect(draw, 215 - ((abs(above[strike]) / maxAbove) * 150), x, 215, x + 12, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			if (above2[strike] != 0) : drawRect(draw, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x, 215, x + 2, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			if (upper[strike] != 0) : drawRect(draw, 399 - ((upper[strike] / maxUpper) * 100), x, 399, x + 12, color="#0f0", border='')
			#if (lower[strike] != 0) : drawRect(draw, 401 + ((lower[strike] / maxLower) * 100), x, 401, x + 12, color="#f00", border='')
			if (lower[strike] != 0) : drawRect(draw, 401, x, 401 + ((lower[strike] / maxLower) * 100), x + 12, color="#f00", border='')
			for kl in keyLevels:
				if strike == kl: drawPointer(draw, 218 + font.getmask(str(strike)).getbbox()[2], x + 8, "#77F")
			if strike == strikes.ClosestStrike: drawPointer(draw, 218 + font.getmask(str(strike)).getbbox()[2], x + 8, "#FF7")
			
		x = 0
	else :
		x = -15
		for strike in sorted(strikes.Strikes) :
			x += FONT_SIZE - 3
			drawRotatedText(img, x=x - 5, y=220, txt=str(round(strike, 2)), color="#F00" if strike == maxPain else "#CCC")   #color needs to change on rotated text.....
			if (top[strike] != 0) : drawRect(draw, x, 0, x + 12, ((top[strike] / maxTop) * 65), color="#00F", border='')
			if (above[strike] != 0) : drawRect(draw, x, 215 - ((abs(above[strike]) / maxAbove) * 150), x + 12, 215, color=("#0f0" if (above[strike] > -1) else "#f00"), border='')
			if (above2[strike] != 0) : drawRect(draw, x, 215 - ((abs(above2[strike]) / maxAbove2) * 150), x + 2, 215, color=("#077" if (above2[strike] > -1) else "#f77"), border='')
			if (upper[strike] != 0) : drawRect(draw, x, 399 - ((upper[strike] / maxUpper) * 100), x + 12, 399, color="#0f0", border='')
			if (lower[strike] != 0) : drawRect(draw, x, 401 + ((lower[strike] / maxLower) * 100), x + 12, 401, color="#f00", border='')
			if strike == strikes.ClosestStrike: drawPriceLine(draw, x + 10 if strikes.Price > strikes.ClosestStrike else x, "#FF0")
			if strike == zero : drawPriceLine(draw, x + 5, "#FFF")
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

		y = 0
		if chartType == CHART_ROTATE :
			x = x + 280
		else: 
			y = FONT_SIZE * 5
		drawText(draw, x=x, y=y, txt="Zero Gamma "+"${:,.2f}".format(zero), color="orange")
		drawText(draw, x=x, y=y + FONT_SIZE, txt="Zero Delta " + "${:,.2f}".format(zeroD), color="#0FF")
		drawText(draw, x=x, y=y + (FONT_SIZE * 2), txt="MaxPain ${:,.2f}".format(maxPain), color="#F00")
		
	img.save("stock-chart.png")
	return "stock-chart.png"

def drawPointer(draw, x, y, clr):
	draw.polygon([(x,y), (x + 15,y - 7), (x + 15, y + 7)], fill=clr, outline=clr)

def drawIVText(img, x, y, txt, color):
	text_layer = PILImg.new('L', (100, FONT_SIZE))
	dtxt = ImageDraw.Draw(text_layer)
	dtxt.text( (0, 0), txt, fill=255, font=font)
	rotated_text_layer = text_layer.rotate(270.0, expand=1)
	PILImg.Image.paste( img, rotated_text_layer, (x,y) )

def loadIVLog(ticker_name):
	fileName = ticker_name + "-IV.json"
	if not exists(fileName):  
		with open(fileName, "w") as outfile:  
			outfile.write('{"IVData": "SPX"}')   #File Must have contents for JSON decoder
	try:
		data = json.load(open(fileName,'r'))
	except:
		print('Check file contents ', fileName)
		return {}
	return data

def zero_gex(data, price):
	def add(a, b): return (b[0], a[1] + b[1])
	strikes = [] #convert data dict to the tuples list function requires
	for d in data : strikes.append( (d, data[d]) )   # list(strike, GEX)
	cumsum = list(accumulate(strikes, add)) #each elements gamma is added to the one after it
	a = min(cumsum, key=lambda i: i[1])[0]
	b = max(cumsum, key=lambda i: i[1])[0]
	return a
	#return a if abs(a - price) < abs(b - price) else b

def algoLevels(ticker):
	#atrs = getATRLevels(ticker)
	nodes = getOOPS(ticker, 0, 40, CHART_LOG)
	keyLevels = []
	mostOI = 0
	mostOIStrike = nodes.Strikes[0]
	for s in nodes.Strikes:
		gex = nodes.Calls[s].GEX - nodes.Puts[s].GEX
		dex = nodes.Calls[s].DEX + nodes.Puts[s].DEX
		if ((gex < 0) and (dex > 0)) or ((gex > 0) and (dex < 0)) :
			keyLevels.append( s )
		tmp = nodes.Calls[s].OI + nodes.Puts[s].OI
		if tmp > mostOI:
			mostOI = tmp
			mostOIStrike = s
	keyLevels.append( mostOIStrike )
	gex = {}
	for i in sorted(nodes.Strikes) : gex[i] = nodes.Calls[i].GEX - nodes.Puts[i].GEX
	keyLevels.append( zero_gex( gex , nodes.Price ) )
	
	print( keyLevels )
#algoLevels("SPX")


"""
  calcVannaEx(
                level,
                df["StrikePrice"],
                df["PutIV"],
                df["daysTillExp"],
                yield_10yr,
                dividend_yield,
                "put",
                df["PutOpenInt"],
            ),
def calcVannaEx(S, K, vol, T, r, q, optType, OI):
    dp = (np.log(S / K) + (r - q + 0.5 * vol**2) * T) / (vol * np.sqrt(T))
    dm = dp - vol * np.sqrt(T)
    if optType == "call":
        vanna = -np.exp(-q * T) * norm.pdf(dp) * (dm / vol)
        # change in delta per one percent move in IV
        # or change in vega per one percent move in underlying
        return OI * 100 * vol * 100 * vanna
    else:  # Vanna is same formula for calls and puts
        vanna = -np.exp(-q * T) * norm.pdf(dp) * (dm / vol)
        return OI * 100 * vol * 100 * vanna

            calcCharmEx(
                level,
                df["StrikePrice"],
                df["CallIV"],
                df["daysTillExp"],
                yield_10yr,
                dividend_yield,
                "call",
                df["CallOpenInt"],
            ),
def calcCharmEx(S, K, vol, T, r, q, optType, OI):
    dp = (np.log(S / K) + (r - q + 0.5 * vol**2) * T) / (vol * np.sqrt(T))
    dm = dp - vol * np.sqrt(T)
    if optType == "call":
        charm = (q * np.exp(-q * T) * norm.cdf(dp)) - np.exp(-q * T) * norm.pdf(dp) * (
            2 * (r - q) * T - dm * vol * np.sqrt(T)
        ) / (2 * T * vol * np.sqrt(T))
        return OI * 100 * T * charm  # change in delta per day until expiration
    else:
        charm = (-q * np.exp(-q * T) * norm.cdf(-dp)) - np.exp(-q * T) * norm.pdf(
            dp
        ) * (2 * (r - q) * T - dm * vol * np.sqrt(T)) / (2 * T * vol * np.sqrt(T))
        return OI * 100 * T * charm
"""


"""
previous_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&periodType=day&period={days}&frequencyType=minute&frequency=1"
today_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&frequencyType=minute&frequency=1&endDate=1915362000000&startDate={start_date}&needExtendedHoursData=true"

def getTimeMilliseconds( days ):
	today = datetime.date.today()
	if today.weekday() > 4 : today = today - datetime.timedelta(days=(today.weekday() % 4))
	today = today - datetime.timedelta(days= days)
	return int(round(time.mktime(today.timetuple()) * 1000))

def getCandles( ticker, days ):
	url_endpoint = today_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker.upper(), start_date=getTimeMilliseconds(int(days)))
	return json.loads(requests.get(url=url_endpoint, headers=HEADER).content)

def clickButton():
	global canvas
	canvas.create_rectangle(0, 0, 2000, IMG_H, fill='black')

	drawTickerOnCanvas( e1.get().upper(), e2.get(), "orange" )

	#drawTickerOnCanvas( "$SPX.X", e2.get(), "yellow" )
	#drawTickerOnCanvas( "$VIX.X", e2.get(), "white" )
	#drawTickerOnCanvas( "TLT", e2.get(), "orange" )
#	drawTickerOnCanvas( "DXY", e2.get(), "purple" )

def drawTickerOnCanvas( ticker, days, color ):
	global canvas
	#{'open': 450.9499, 'high': 450.9499, 'low': 450.89, 'close': 450.92, 'volume': 2493, 'datetime': 1693612740000}
	highPrice = 0
	lowPrice = 9999999
	candles = getCandles(ticker, days)['candles']
	avgs = []
	for i in range( len( candles ) ) :
		avgs.append( (candles[i]['high'] + candles[i]['low']) / 2 )
		if avgs[i] > highPrice : highPrice = avgs[i]
		if avgs[i] < lowPrice : lowPrice = avgs[i]
	priceRange = highPrice - lowPrice
	scale = IMG_H / priceRange
	
	lenavgs = len(avgs)
	
	highs = []
	lows = []
	last = avgs[0]
	high = 0
	low = 0
	def checkNextHigh(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] > avgs[index] : return False
		return True
	def checkNextLow(index):
		last = index + 10 if index + 10 < lenavgs else lenavgs
		for i in range(index, last):
			if avgs[i] < avgs[index] : return False
		return True

	for i in range( 1, lenavgs ) :
		if avgs[i] > avgs[high] and checkNextHigh(i):
			highs.append(i)
			high = i
			low = i
		elif avgs[i] < avgs[low] and checkNextLow(i):
			lows.append(i)
			low = i
			high = i
		else:
			pass

	def convertY( val ):	return IMG_H - ((val - lowPrice) * scale)
	if lenavgs > 2000 : lenavgs = 2000
	for x in range( 1, lenavgs ):
		y1 = convertY(avgs[x-1])
		y2 = convertY(avgs[x])
		canvas.create_line(x-1,y1,x,y2, fill=color, width=1)
		
#		if x in highs : canvas.create_line(x-5,convertY(avgs[x]),x+5,convertY(avgs[x]), fill="green", width=5)
#		if x in lows : canvas.create_line(x-5,convertY(avgs[x]),x+5,convertY(avgs[x]), fill="red", width=5)

	for x in range(1, len(highs)):
		canvas.create_line(highs[x-1],convertY(avgs[highs[x-1]]),highs[x],convertY(avgs[highs[x]]), fill="green", width=1)
	for x in range(1, len(lows)):
		canvas.create_line(lows[x-1],convertY(avgs[lows[x-1]]),lows[x],convertY(avgs[lows[x]]), fill="red", width=1)

	
from tkinter import *
win = Tk()
win.geometry(str(2000 + 5) + "x" + str(IMG_H + 45))

Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

e1 = Entry(win, width=8)
e1.grid(row=0, column=0, sticky='E')
e1.insert(0, "SPY")

e2 = Entry(win, width=4)
e2.grid(row=0, column=1, sticky='E')
e2.insert(0, '2')

Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
Button(win, text="Fetch", command=clickButton, width=5).grid(row=0, column=2, sticky='E')
#Button(win, text="Loop", command=gui_click_loop, width=5).grid(row=0, column=3, sticky='N')

canvas = Canvas(win, width=2000, height=IMG_H)
canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
canvas.configure(bg="#000000")

clickButton()
mainloop()
"""

thread_discord()

"""
beginning we were neg gamma which means illiquidity in the market overall, going to positive gamma afternoon but with flat PA means MMs still held their hedges from the neg gamma env, then going positive gamma with no downtrend means explosive rally upside due to the compounding effect of the hedge unwind)
By illiquidity i mean the transaction around a strike goes down as in not enough buyers sellers so a skew of buyers vs sellers is created which can create a feedback loop
"""