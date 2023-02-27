#Open this url in a browser, it directs you to TDA login page, HTTP server running fetches the Auth Code, and retrieves Auth/Refresh tokens.  You can disable the HTTPServer for 90 days if wanted
#https://auth.tdameritrade.com/oauth?client_id=(YOUR_API_KEY_HERE)%40AMER.OAUTHAP&response_type=code&redirect_uri=https%3A%2F%2Flocalhost%3A8080%2F


#    This software is completely free to use, modify, or anything else you want
#    Copyright (C) 2022 Seth Mayberry

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
import logging
import threading
import sys
from colour import Color
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

#import logging
 
# Create and configure logger
#logging.basicConfig(filename="newfile.log", format='%(asctime)s %(message)s',  filemode='w')
 
# Creating an object
#logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
#logger.setLevel(logging.DEBUG)


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
history_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/pricehistory?apikey={api_key}&periodType=day&period=1&frequencyType=minute&frequency=1&needExtendedHoursData=true"
price_endpoint = "https://api.tdameritrade.com/v1/marketdata/{stock_ticker}/quotes?apikey={api_key}"   # %24 is a $  aka $VIX.X
auth_endpoint = "https://api.tdameritrade.com/v1/oauth2/token?apikey={api_key}"

CHART_NORMAL = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_TIMEVALUE = 3
CHART_ROTATE = 4
CHART_JSON = 5

FONT_SIZE = 22
STR_FONT_SIZE = str(int(FONT_SIZE / 2))  #strangely font size is 2x on tkinter canvas
font = ImageFont.truetype("Arimo-Regular.ttf", FONT_SIZE, encoding="unic") #Place font file in same folder, or use supply path if needed in Linux

IMG_W = 1000
IMG_H = 500
IMG_W_2 = IMG_W / 2
IMG_H_2 = IMG_H / 2
ticker_name = 'SPY'
GEX = {}
DEX = {}
CallIV = {}
PutIV = {}
CallOI = {}
PutOI = {}
CallGEX = {}
PutGEX = {}
CallATM = 0
PutATM =0
CallDollars = 0.0
PutDollars = 0.0
ExpectedMove = 0.0
atmDif = 999
closestStrike = 0
CallATMIV = {}
PutATMIV = {}
IVUpdateChannel = []
IVUpdateChannelCounter = 0

#Generate a color gradient between red and green, used to rate fundamentals and look cool doing it
red = Color("#FF0000")
colorGradient = list(red.range_to(Color("#00FF00"),10))
colorGradient[0] = "#FF0000"
colorGradient[9] = "#00FF00"

img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
draw = ImageDraw.Draw(img)

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
SockThread.start() 
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
headers = { "Authorization": "Bot " + BOT_TOKEN} #headers = { "Authorization": "Bearer " + BOT_CLIENT_ID }
slash_command_json = {
    "name": "gex", "type": 1, "description": "Draw a GEX/DEX chart", "options": [ { "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, { "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, { "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [{ "name": "Normal", "value": "Normal"  }, { "name": "Rotated", "value": "R" }, { "name": "Volume", "value": "V" }, { "name": "TimeValue", "value": "TV"  }, { "name": "IV", "value": "IV"  }, { "name": "JSON", "value": "JSON"  }]}   ] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = { "name": "8ball", "type": 1, "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }],
    "name": "help", "type": 1, "description": "Provides help for Smayxor",
    "name": "sudo", "type": 1, "description": "Shuts off Smayxor", "options":[{ "name": "command", "description": "Super User ONLY!", "type": 3, "required": True }] }
print( requests.post(url, headers=headers, json=slash_command_json) )

slash_command_json = {    
    "name": "tits", "type": 1, "description": "Show me the titties!", "options":[{ "name": "extra", "description": "extra", "type": 3, "required": False }], 
    "name": "ass", "type": 1, "description": "Check out the shitter on that critter!", "options":[{ "name": "extra", "description": "extra", "type": 3, "required": False }],
    "name": "gm", "type": 1, "description": "GM Frens", "options":[{ "name": "extra", "description": "extra", "type": 3, "required": False }],
    "name": "pump", "type": 1, "description": "PUMP IT UP!!!", "options":[{ "name": "extra", "description": "extra", "type": 3, "required": False }],
    "name": "dump", "type": 1, "description": "BEAR MARKET BITCH!!!", "options":[{ "name": "extra", "description": "extra", "type": 3, "required": False }]
}
print( requests.post(url, headers=headers, json=slash_command_json) )

#Removes slash commands
#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/1078392146064838738", headers=headers) )   

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
bot = commands.Bot(command_prefix='}', intents=intents, help_command=None, sync_commands=True)
def thread_discord():
    strHelp = """}? for commands for Smayxor
}s ticker dte, you can leave out DTE for 0DTE.  Can also use /gex ticker dte charttype
/8ball followed by a question, ending in ?
The top bars are OI.
The Red/Green bars above the strikes are Total Gamma Exposure, with blue/pink DEX lines.
Under the strikes is Call Put GEX individually
Additional Chart Types are V for volume, IV for ImpliedVolatility, R for rotated, and TV for TimeValue
}s spx 0 v    for a volume chart
Smayxor has switched to using /gex"""

    def getChartType( arg ):
        arg = arg.upper()
        if arg == 'V': return CHART_VOLUME
        elif arg == 'IV': return CHART_IV
        elif arg == 'TV': return CHART_TIMEVALUE
        elif arg == 'R': return CHART_ROTATE
        elif arg == 'JSON': return CHART_JSON
        else: return CHART_NORMAL

    @bot.tree.command(name="gex", description="Draws a GEX chart")
    async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, chart: str = "NORMAL"):   
        global tickers, updateRunning, counter, auto_updater, IVUpdateChannel, IVUpdateChannelCounter, CallATMIV, PutATMIV
        await intr.response.send_message("Fetching GEX chart for " + ticker) 
        tickers.append( (ticker.upper(), dte, getChartType(chart), intr.channel.id, intr.channel) )
        if updateRunning == False :
            print("Starting queue")
            updateRunning = True
            channelUpdate.start()        

    @bot.tree.command(name="pump")
    async def slash_command_pump(intr: discord.Interaction, extra: str = "pump"):
        if random.random() < 0.91 :
            await intr.response.send_message( getTenorGIF( random.choice(pumps) + enc(" " + extra) ) )
        else:
            await intr.response.send_message(file=discord.File(random.choice(["./pepe-money.gif", "./wojak-pump.gif"])))
            
    @bot.tree.command(name="dump")
    async def slash_command_dump(intr: discord.Interaction, extra: str = "dump"):
        await intr.response.send_message( getTenorGIF( random.choice(dumps) + enc(" " + extra) ) )

    @bot.tree.command(name="tits")
    async def slash_command_tits(intr: discord.Interaction, extra: str = "tits"):
        await intr.response.send_message( getTenorGIF( random.choice(titties) + enc(" " + extra) ) )

    @bot.tree.command(name="ass")
    async def slash_command_ass(intr: discord.Interaction, extra: str = "ass"):
        await intr.response.send_message( getTenorGIF( random.choice(asses) + enc(" " + extra) ) )

    @bot.tree.command(name="gm")
    async def slash_command_gm(intr: discord.Interaction, extra: str = "gm"):
        if random.random() < 0.91 :
            await intr.response.send_message( getTenorGIF( random.choice(gms) + enc(" " + extra) ) )
        else:
            await intr.response.send_message(file=discord.File('./bobo-gm-frens.gif'))

    @bot.tree.command(name="8ball", description="Answers your question?")
    async def slash_command_8ball(intr: discord.Interaction, question: str):   
        future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good']
        if "?" in question: await intr.response.send_message("Question: " + question + "\rAnswer: " + random.choice(future))
        else: await intr.response.send_message("Please phrase that as a question")

    @bot.tree.command(name="sudo")
    @commands.is_owner()
    async def slash_command_sudo(intr: discord.Interaction, command: str):
        global tickers, updateRunning, counter, auto_updater, IVUpdateChannel, IVUpdateChannelCounter, CallATMIV, PutATMIV
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
            dte = args[2] if (len(args) == 3) and args[2].isnumeric() else '0'
            chart = getChartType(args[3]) if (len(args) == 4) else 'NORMAL' 
            print("Appending to Auto_Updater array :", args[1], dte, chart, intr.channel.id)
            auto_updater.append( (args[1], dte, chart, intr.channel.id, intr.channel) )
            if updateRunning == False :
                print("Starting queue")
                updateRunning = True
                channelUpdate.start()
            await intr.response.send_message(user + " started auto-update on " + args[1])
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
  
    @bot.tree.command(name="help")
    async def slash_command_help(intr: discord.Interaction):
        await intr.response.send_message(strHelp)
  
    @bot.command(name="?")
    async def question(ctx):
        await ctx.send(strHelp)

    @tasks.loop(seconds=1)
    async def channelUpdate():
        global tickers, counter, auto_updater, IVUpdateChannel, IVUpdateChannelCounter
        if len(tickers) != 0 :
            for tck in tickers:
                fn = stock_price(tck[0], tck[1], tck[2])
                chnl = bot.get_channel(tck[3])
                if chnl == None : chnl = tck[4]
                if fn == "error.png": await chnl.send("Failed to get data for " + tck[0])
                else: await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
                tickers.clear()
        if len(auto_updater) != 0:
            counter += 1
            if counter > 300 :
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
    async def question(ctx, *args):
        global tickers, updateRunning
        print( "Command }s ", args )
        if ctx.message.author == bot.user: return
        if len(args) == 0: return
        dte = (args[1] if (len(args) > 1) and args[1].isnumeric() else '0')
        tickers.append( (args[0].upper(), dte, getChartType(args[2]) if (len(args) == 3) else 0, ctx.message.channel.id, ctx.message.channel) )
        if updateRunning == False :
            print("Starting queue")
            updateRunning = True
            channelUpdate.start()
    """
    @bot.event #await bot.process_commands(message)
    async def on_message(message):  #handling bot commands myself so we can do ALL stocks with optional dte arguement
        global tickers, updateRunning, counter, auto_updater, IVUpdateChannel, IVUpdateChannelCounter, CallATMIV, PutATMIV
        if message.author == bot.user: return
        if len(message.content) == 0: return
        if message.content[0] != '}': return
        args = message.content.split(' ')
        if (len(args[0]) == 1): return
        args[0] = args[0].split('}')[1]

        ticky = args[0].upper()
        dte = args[1] if (len(args) > 1) and args[1].isnumeric() else '0'
        print(message.channel.id)
        tickers.append( (ticky, dte, getChartType(args[2]) if (len(args) == 3) else 0, message.channel.id, message.channel) )
        if updateRunning == False :
            print("Starting queue")
            updateRunning = True
            channelUpdate.start()
    """                
    bot.run(BOT_TOKEN)

def rateFundamental(ticker_name, fundamental, value):
    rating = 5
    try:
        if 'Calls' in fundamental:
            rating = 9
        elif 'Puts' in fundamental:
            rating = 0
        elif 'Total' in fundamental:
            total = CallDollars - PutDollars
            rating = 9 if total > (CallDollars * 0.25) else 0 if abs(total) > (PutDollars * 0.25) else 5
    except:
        rating = 5
    if rating < 0: rating = 0
    if rating > 9: rating = 9
    if (ticker_name in fundamental) or ("DTE" in str(value)): color = "#0FF"
    else: color = colorGradient[int(rating)]
    return color

def drawRect(x, y, w, h, color, border):
    if border in 'none': border = color
    draw.rectangle([x,y,w,h], fill=color, outline=border)   #for PIL Image

def drawPriceLine(x, color):  #Draws a dashed line
    y = 100
    while y < 350:
        draw.line([x, y, x, y + 4], fill=color, width=1)
        y += 6

def drawRotatedPriceLine(y, color):  #Draws a dashed line
    x = 120
    while x < 350:
        draw.line([x, y, x + 4, y], fill=color, width=1)
        x += 6

def drawText(x, y, txt, color):
    draw.text((x,y), text=txt, fill=color, font=font) 

def drawRotatedText(x, y, txt, color):  
    text_layer = PILImg.new('L', (100, FONT_SIZE))
    dtxt = ImageDraw.Draw(text_layer)
    dtxt.text( (0, 0), txt, fill=255, font=font)
    rotated_text_layer = text_layer.rotate(270.0, expand=1)
    PILImg.Image.paste( img, rotated_text_layer, (x,220) ) 

def clearScreen():
    img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
    drawRect(0,0,IMG_W,IMG_H, color="#000", border="#000")

def getFundamentals(ticker_name):    
    try:
        page = requests.get(url=fundamental_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name))
        content = json.loads(page.content)[ticker_name]["fundamental"]
        result = {'Beta': content["beta"], 'DivYield': content["dividendYield"], 'DivDate': content["dividendDate"], 'DivAmount': content["dividendAmount"], 'peRatio': content["peRatio"], 'pegRatio': content["pegRatio"], 'QuickRatio': content["quickRatio"], 'DebtToCapital': content["totalDebtToCapital"], 'SharesOut': f'{int(content["sharesOutstanding"]):,}', 'Float': f'{(int(content["marketCapFloat"]) * 1000000):,}', 'MCap': f'{(int(content["marketCap"]) * 1000000):,}'}
        return result
    except :
        return {'Bad Ticker' : 'Tell Smayberry'}         
    
def addStrike(strike, volume, oi, delta, gamma, vega, price, volatility, call, itm, bid, days, chartType, timeValue):
    global GEX, DEX, CallIV, PutIV, CallOI, PutOI, CallDollars, PutDollars, atmDif, closestStrike, CallATM, PutATM
    try:
        if not strike in GEX: newStrike(strike)  #Prevents NaN values?
        if chartType == CHART_NORMAL :
            a = 1
        if chartType == CHART_VOLUME : 
            oi = volume
        elif chartType == CHART_TIMEVALUE :
            GEX[strike] = timeValue
            if (call == 1):
                CallGEX[strike] = timeValue
            else:
                PutGEX[strike] = timeValue                  
            return
        if (oi == 0): return 0  #Delta and Gamma show up as -999.0
        if (delta > 990) or (delta < -990) : return #need to test values for NaN
        
        GEX[strike] += (gamma * oi * call)
        DEX[strike] += (delta * oi)

        if (call == 1):
            CallIV[strike] = volatility
            CallGEX[strike] += (gamma * oi)
            CallDollars += (bid * oi)
            CallOI[strike] += oi
        else:
            PutIV[strike] = volatility
            PutGEX[strike] += (gamma * oi)
            PutDollars += (bid * oi)
            PutOI[strike] += oi
              
        distToMoney = (abs(strike - price))
        if distToMoney < atmDif: 
            atmDif = distToMoney
            closestStrike = strike
       
#def daysFromNow(days):
#    dn = datetime.datetime.now()
#    dn = dn.replace(hour=0, minute=0, second=0, microsecond=0)
#    delta = dt.strptime(days.split(":")[0], "%Y-%m-%d") - dn
#    return delta.days
        if closestStrike == strike : 
            if call == 1 : CallATM = bid
            else : PutATM = bid

        return oi
    except:
        return 0

def newStrike(strike):
    global GEX, DEX, CallIV, PutIV, CallOI, PutOI
    GEX[strike] = 0
    CallGEX[strike] = 0
    PutGEX[strike] = 0
    DEX[strike] = 0
    CallIV[strike] = 0
    PutIV[strike] = 0
    CallOI[strike] = 0
    PutOI[strike] = 0

def clearArrays():
    global ExpectedMove, GEX, DEX, CallIV, PutIV, CallOI, PutOI, CallATM, PutATM, CallDollars, PutDollars, atmDif, closestStrike
    GEX.clear()
    CallGEX.clear()
    PutGEX.clear()
    DEX.clear()
    CallIV.clear()
    PutIV.clear()
    CallOI.clear()
    PutOI.clear()
    CallATM = 0
    PutATM = 0
    ExpectedMove = 0.0
    CallDollars = 0.0
    PutDollars = 0.0
    atmDif = 999
    closestStrike = 0

def drawCharts(ticker_name, dte, price, chartType):
    global ExpectedMove, GEX, DEX, CallIV, PutIV, CallOI, PutOI, CallDollars, PutDollars, FONT_SIZE, closestStrike, draw, img
#Get max GEX/DEX for math to draw chart,  alternative would be to make a'MAX' key in each array
    maxOI = 1
    maxGEX = 0
    maxDEX = 0
    maxCPGEX = 0
    for strikes in GEX:
        if abs(GEX[strikes]) > maxGEX: maxGEX = abs(GEX[strikes])
        if abs(CallGEX[strikes]) > maxCPGEX: maxCPGEX = abs(CallGEX[strikes])
        if abs(PutGEX[strikes]) > maxCPGEX: maxCPGEX = abs(PutGEX[strikes])
        if abs(DEX[strikes]) > maxDEX: maxDEX = abs(DEX[strikes])
              
        #CallOI[strikes] += PutOI[strikes]   #Combining for a total.  Individual OI looks a lot like gamma chart
        if abs(CallOI[strikes]) > maxOI: maxOI = abs(CallOI[strikes])
        if abs(PutOI[strikes]) > maxOI: maxOI = abs(PutOI[strikes])

#    vix = json.loads(requests.get(url=vix_endpoint.format(api_key=MY_API_KEY)).content)['$VIX.X']['lastPrice']
    fundamentals = {}
    fundamentals[ticker_name] = "$" + str(price) + " : " + dte.split(":")[1] + " DTE"
#    fundamentals['VIX'] = "{:,.2f}".format(vix)
    fundamentals['ExpectedMove'] = "$" + str(round(ExpectedMove, 2))
    fundamentals['Calls'] = "${:,.2f}".format(CallDollars)
    fundamentals['Puts'] = "${:,.2f}".format(PutDollars)
    fundamentals['Total'] = "${:,.2f}".format(CallDollars - PutDollars)
    if (chartType == CHART_NORMAL) or (chartType == CHART_ROTATE) : fundamentals['ChartType'] = "GEX "
    if chartType == CHART_VOLUME : fundamentals['ChartType'] = "Volume "
    if chartType == CHART_IV : fundamentals['ChartType'] = "IV "
    if chartType == CHART_TIMEVALUE : fundamentals['ChartType'] = "TimeValue "

    #Draw the chart
    if chartType == CHART_ROTATE :
        img = PILImg.new("RGB", (IMG_H, IMG_W), "#000")
        draw = ImageDraw.Draw(img)

        text = fundamentals['ChartType'] + ticker_name + " " + fundamentals[ticker_name] + " ExpMove " + fundamentals['ExpectedMove']
        drawText( 2, 2, txt=text, color="#7fF")
        text = "Calls " + fundamentals['Calls']
        drawText( 2, 25, txt=text, color="#7F7")
        text = "Puts " +  fundamentals['Puts']
        drawText( 250, 25, txt=text, color="#F77")
        text = "Total " + fundamentals['Total']
        drawText( 2, 45, txt=text, color="#0FF")
        y = 60
        for strikes in reversed(sorted(GEX)):
            y += FONT_SIZE - 3
            drawText(245, y - 5, txt=str(strikes).replace('.0', ''), color="#CCC")
            yOIc = ((abs(CallOI[strikes]) / maxOI) * 45)
            yOIp = ((abs(PutOI[strikes]) / maxOI) * 45)
            if (CallOI[strikes] != 0): drawRect(yOIp + 1, y, yOIc + yOIp, y + 12, color="#0F0", border='')
            if (PutOI[strikes] != 0): drawRect(0, y, yOIp, y + 12, color="#F00", border='')

            if (GEX[strikes] != 0): drawRect(235 - ((abs(GEX[strikes]) / maxGEX) * 150), y, 235, y + 12, color=("#0f0" if (GEX[strikes] > -1) else "#f00"), border='')
            if (DEX[strikes] != 0): drawRect(235 - ((abs(DEX[strikes]) / maxDEX) * 150), y, 235, y + 2, color=("#077" if (DEX[strikes] > -1) else "#f77"), border='')
            if (CallGEX[strikes] != 0): drawRect(419 - ((CallGEX[strikes] / maxCPGEX) * 100), y, 419, y + 12, color="#0f0", border='')
            if (PutGEX[strikes] != 0): drawRect(421 + ((PutGEX[strikes] / maxCPGEX) * 100), y, 421, y + 12, color="#f00", border='')

            if strikes == closestStrike:
                if price > closestStrike : drawRotatedPriceLine(y, "#FF0")
                else : drawRotatedPriceLine(y + 17, "#FF0")

    else :    # Normal sideways chart
        img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
        draw = ImageDraw.Draw(img)

                  #    clearScreen()    
        x = -15
        for strikes in sorted(GEX):
            x += FONT_SIZE - 3
            drawRotatedText(x=x - 5, y=205, txt=str(strikes).replace('.0', ''), color="#03F3")
            yOIc = ((abs(CallOI[strikes]) / maxOI) * 50)
            yOIp = ((abs(PutOI[strikes]) / maxOI) * 50)
            if (CallOI[strikes] != 0): drawRect(x, yOIp + 1, x + 12, yOIc + yOIp, color="#0F0", border='')
            if (PutOI[strikes] != 0): drawRect(x, 0, x + 12, yOIp, color="#F00", border='')

            if (GEX[strikes] != 0): drawRect(x, 215 - ((abs(GEX[strikes]) / maxGEX) * 150), x + 12, 215, color=("#0f0" if (GEX[strikes] > -1) else "#f00"), border='')
            if (DEX[strikes] != 0): drawRect(x, 215 - ((abs(DEX[strikes]) / maxDEX) * 150), x + 2, 215, color=("#077" if (DEX[strikes] > -1) else "#f77"), border='')
            if (CallGEX[strikes] != 0): drawRect(x, 399 - ((CallGEX[strikes] / maxCPGEX) * 100), x + 12, 399, color="#0f0", border='')
            if (PutGEX[strikes] != 0): drawRect(x, 401 + ((PutGEX[strikes] / maxCPGEX) * 100), x + 12, 401, color="#f00", border='')

            if strikes == closestStrike:
                if price > closestStrike : drawPriceLine(x + 10, "#FF0")
                else : drawPriceLine(x, "#FF0")
#        text = fundamentals['ChartType'] + ticker_name + " " + fundamentals[ticker_name] + " ExpMove " + fundamentals['ExpectedMove']
#        drawText( 2, 475, txt=text, color="#7fF")
#        text = "Calls " + fundamentals['Calls'] + " : Puts " +  fundamentals['Puts'] + " : Total " + fundamentals['Total']
#        drawText( 2, 280, txt=text, color="#7F7")
        x = IMG_W - 250
        drawRect(x, 0, IMG_W, IMG_H, color="#000", border="#777")
        x += 4
        y = 5
        for keys in fundamentals:
            drawText(x, y, txt=keys + ": " + str(fundamentals[keys]), color= str(rateFundamental(ticker_name, keys, fundamentals[keys])) )
            y += FONT_SIZE
                  
def daysFromNow(days):
    dn = datetime.datetime.now()
    dn = dn.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = dt.strptime(days.split(":")[0], "%Y-%m-%d") - dn
    return delta.days

def stock_price(ticker_name, dte, chartType = 0):
    global ExpectedMove, GEX, DEX, CallIV, PutIV, CallOI, PutOI, img, draw, CallDollars, PutDollars, CallATM, PutATM
    clearArrays()
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
            loopAgain = False        #loopAgain = True
#            log = "./logs/" + str(logCounter) + "log.json"
#            with open(log, "w") as outfile:
#                outfile.write(json.dumps(content))
#            sleep(180)
#            logCounter += 1
    if ('error' in content) or (errorCounter == 5) or (content['status'] in 'FAILED'): #Failed, we tried our best
        clearScreen()
        drawText(0,0,txt="Failed to get data", color="#FF0")
        img.save("error.png")
        return "error.png"
    price = content['underlyingPrice']   #underlyingprice == 0.0  same as   status == FAILED
    
#Load the data from JSON
    totalOI = 0
    if chartType == CHART_JSON :
        ticker_name = ticker_name + ".json"
        with open(ticker_name, "w") as outfile:
            outfile.write(json.dumps(content, indent=4))
        return ticker_name
    
    
    for days in content['callExpDateMap']: 
        for strikes in content['callExpDateMap'][days]:
            def addData(opts): 
                try:
                    addStrike(strike=opts["strikePrice"], volume=opts["totalVolume"], oi=opts["openInterest"], delta=opts['delta'], gamma=opts["gamma"], vega=opts['vega'], volatility=opts['volatility'], price=price, call=(1 if (opts['putCall'] in "CALL") else -1), itm=opts['inTheMoney'], bid=opts['bid'], days=days, chartType=chartType, timeValue=opts['timeValue'])
                except:
                  print( 'NaN')
            try:
                for options in content['callExpDateMap'][days][strikes]: addData(options)
                for options in content['putExpDateMap'][days][strikes]: addData(options)
            except:
                  print("No Strike")
    
    #performing $ calcs out here to avoid doing in a loop
    CallDollars = CallDollars * price
    PutDollars = PutDollars * price
              
    ExpectedMove = (CallATM + PutATM) * 0.85

                  
                  
                  
                  
#    print(closestStrike)              
#    for strikes in CallIV:
#        print( CallIV[strikes] , " / ", PutIV[strikes] )

                  
    if (chartType == CHART_IV) :     #CHECK IF STRIKE EXISTS, SPX FUCKS THIS UP
        IVTime = datetime.datetime.now().strftime("%H:%M")
        print( IVTime )
        GEX = {}
        if (CallIV.get(closestStrike) == None) or (PutIV.get(closestStrike) == None): return
        CallATMIV[IVTime] = (CallIV[closestStrike] + CallIV[closestStrike + 1]) / 2
        PutATMIV[IVTime] = (PutIV[closestStrike] + PutIV[closestStrike + 1]) / 2
        for times in CallATMIV:
            
            GEX[times] = CallATMIV[times]
            CallOI[times] = 0
            PutOI[times] = 0
            CallGEX[times] = CallATMIV[times]
            PutGEX[times] = PutATMIV[times]
            DEX[times] = 0
        if len(CallATMIV) > 30: 
            k = next(iter(CallATMIV))
            CallATMIV.pop(k)
            PutATMIV.pop(k)
            #(k := next(iter(d)), d.pop(k))
    
    #Uses days from the for loops above to get last date in list
    drawCharts(ticker_name=ticker_name, dte=days, price=price, chartType=chartType)
    img.save("stock-chart.png")
    return "stock-chart.png"
    
#*************Main "constructor" for GUI, starts thread for Server ********************
thread_discord()
