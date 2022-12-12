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

#Version 1.5 Managed to get OAUTH tokens working.  Only drawing on PIL Image, and copying to TKinter Canvas. Rotated strikes prices. Moved lots of data to fundamentals area.  Still need to bot the login page!
#Version 1.4 Made images larger,  gave bot more !commands.  renamed to .py instead of .pyt.  included yahoo finance library yfinance to get company fundamentals.  fundamentals are now "Rated" and colored from Red to Green (rating system needs an overhaul).  Server Mode and GUI Mode option from command prompt
#Version 1.3  Added DISCORD BOT functionality.  Make account in Discord Developer, add an App, give Read Messages,  Send Message, Attach Files permissions.  Add a BOT_TOKEN to the apikey.json
#Version 1.2  Got it to save chart as a png.  Preparing for a discord bot
#Version 1.1  Improved display of data on charts to scale with max values

from datetime import date
from datetime import datetime as dt
import datetime
import time
from time import sleep
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
import yfinance as yf
import urllib.parse
from os.path import exists
from PIL import ImageOps, ImageDraw, ImageGrab, ImageFont
import PIL.Image as PILImg

#import pandas as pd
#import numpy as np
#import scipy
#from scipy.stats import norm
#import matplotlib.pyplot as plt

#************************************************************
#Get API Key from TDA Developer Account new App,  place in file named apikey.json with this for contents-> {"API_KEY": "your-key-here"}
init = json.load(open('apikey.json'))
MY_API_KEY = init['API_KEY']
BOT_TOKEN = init['BOT_TOKEN']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
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

#list of keys for yahoo finance data.  some things have been removed
listOfKeys = "'fullTimeEmployees', 'longBusinessSummary', 'ebitdaMargins', 'profitMargins', 'grossMargins', 'operatingCashflow', 'revenueGrowth', 'operatingMargins', 'ebitda', 'targetLowPrice', 'grossProfits', 'freeCashflow', 'targetMedianPrice', 'currentPrice', 'earningsGrowth', 'currentRatio', 'returnOnAssets', 'targetMeanPrice', 'debtToEquity', 'returnOnEquity', 'targetHighPrice', 'totalCash', 'totalDebt', 'totalRevenue', 'totalCashPerShare', 'revenuePerShare', 'quickRatio', 'recommendationMean', 'annualHoldingsTurnover', 'enterpriseToRevenue', 'beta3Year', 'enterpriseToEbitda', '52WeekChange', 'morningStarRiskRating', 'forwardEps', 'revenueQuarterlyGrowth', 'sharesOutstanding', 'fundInceptionDate', 'annualReportExpenseRatio', 'totalAssets', 'bookValue', 'sharesShort', 'sharesPercentSharesOut', 'fundFamily', 'lastFiscalYearEnd', 'heldPercentInstitutions', 'netIncomeToCommon', 'trailingEps', 'lastDividendValue', 'SandP52WeekChange', 'priceToBook', 'heldPercentInsiders', 'nextFiscalYearEnd', 'yield', 'mostRecentQuarter', 'shortRatio', 'sharesShortPreviousMonthDate', 'floatShares', 'beta', 'enterpriseValue', 'priceHint', 'threeYearAverageReturn', 'lastDividendDate', 'morningStarOverallRating', 'earningsQuarterlyGrowth', 'priceToSalesTrailing12Months', 'dateShortInterest', 'pegRatio', 'ytdReturn', 'forwardPE', 'lastCapGain', 'shortPercentOfFloat', 'sharesShortPriorMonth', 'impliedSharesOutstanding', 'fiveYearAverageReturn', 'twoHundredDayAverage', 'trailingAnnualDividendYield', 'payoutRatio', 'regularMarketDayHigh', 'navPrice', 'averageDailyVolume10Day', 'regularMarketPreviousClose', 'trailingAnnualDividendRate', 'dividendRate', 'exDividendDate', 'trailingPE', 'marketCap','dividendYield'"

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
VEX = {}
Volas = {}
OIS = {}
CallGEX = {}
PutGEX = {}
CallDollars = 0.0
PutDollars = 0.0
ExpectedMove = 0.0
atmDif = 999
closestStrike = 0
dn = datetime.datetime.now()
dn = dn.replace(hour=0, minute=0, second=0, microsecond=0)

#Generate a color gradient between red and green, used to rate fundamentals and look cool doing it
red = Color("#FF0000")
colorGradient = list(red.range_to(Color("#00FF00"),10))
colorGradient[0] = "#FF0000"
colorGradient[9] = "#00FF00"

img = PILImg.new("RGB", (IMG_W, IMG_H), "#000")
draw = ImageDraw.Draw(img)

serverMode = True
guiMode = True
n = len(sys.argv)
if (n > 1) :
    serverMode = sys.argv[1] in "server"
    guiMode = sys.argv[1] in "gui"
print("ServerMode ", serverMode, " / GUIMode ", guiMode)

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


if guiMode: from tkinter import *
if serverMode:
    import discord
    from discord.ext import commands
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='!', intents=intents) #, help_command=None
    def thread_discord():
        
        @bot.command(name="rain")
        async def pump(ctx):
            embed = discord.Embed(title="Imma make it rain", color=0x00ff00) 
            file = discord.File("./pepe-money.gif", filename="pepe-money.gif")
            embed.set_image(url="attachment://pepe-money.gif")
            await ctx.channel.send(file=file, embed=embed)
        
        @bot.command(name="pump")
        async def rain(ctx):
            embed = discord.Embed(title="SUPER SLAM PUMP BUTTON", color=0x00ff00) 
            file = discord.File("./wojak-pump.gif", filename="wojak-pump.gif")
            embed.set_image(url="attachment://wojak-pump.gif")
            await ctx.channel.send(file=file, embed=embed)
        
        @bot.command(name="gm")
        async def gm(ctx):
            #embed.set_image(url="https://media.discordapp.net/stickers/1041335509269618810.png")
            #with open('./bobo-gm-frens.png', 'rb') as fp: 
            #        await ctx.channel.send('Good morning degens', file=discord.File(fp, 'bobo-gm-frens.png'))
            embed = discord.Embed(title="Good morning degens", color=0x00ff00) #You can add a text in there if you             embed = discord.Embed(title="Good morning degens", description="Good morning degens", color=0x00ff00) #You can add a text in there if you want
#            embed.set_footer(text="Good morning degens")
        #embed.add_field(name="**Add something**", value="Or delete this.", inline=False) 
#            embed.set_image(url="https://media.discordapp.net/stickers/1041335509269618810.png")
            #await ctx.author.send(embed=embed) #This sends the message in the DMs change to "ctx.send" to send it in chat
#            await ctx.channel.send(embed=embed)
            file = discord.File("./bobo-gm-frens.gif", filename="bobo-gm-frens.gif")
            embed.set_image(url="attachment://bobo-gm-frens.gif")
            await ctx.channel.send(file=file, embed=embed)
        
        @bot.command(name="8")
        async def eight(ctx, *question): await eightBall(ctx, *question)

        @bot.command(name="8ball")
        async def eightBall(ctx, *question):
            future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good']
            isQuestion = False
            for word in question: isQuestion = isQuestion | ("?" in word)
            if isQuestion:
                await ctx.channel.send(random.choice(future))
            else:
                await ctx.channel.send("Please phrase that as a question")
            
        @bot.command(name="flist")
        async def fundamentalsList(ctx):
            await ctx.channel.send(listOfKeys)
            
        @bot.command(name="fundamentals")
        async def fundamentals(ctx, arg1):
            if len(arg1) > 6 : return # Note, hackers could totally exploit the arg1 to delete any file on ur system
            fileName = "./" + arg1 + ".txt"
            try:
                funds = yf.Ticker(arg1)
                dict = funds.info        
                with open(fileName, 'w') as file:
                    file.write("Fundamentals for " + arg1 + "\n")
                    for data in dict:
                        if data in dict: file.write(data + " - " + str(dict[data]) + "\n")
                with open(fileName, 'rb') as fp: 
                    await ctx.channel.send(file=discord.File(fp, fileName))
            except:
                await ctx.channel.send("Check ticker and fundamental name, try again.")
            os.remove(fileName, dir_fd=None)    
            
        @bot.command(name="fund")
        async def fundamental(ctx, arg1, arg2):
            try:
                funds = yf.Ticker(arg1)
                dict = funds.info
                await ctx.channel.send(arg1.upper() + " " + arg2 + " : " + str(dict[arg2]))
            except:
                await ctx.channel.send("Check ticker and fundamental name, try again.")

        @bot.command(name="kill")
        async def restart_command(ctx):
            print("Shutdown triggered by : ", ctx.author.name, ctx.author.id)
            if BOT_USER_FOR_KILL in ctx.author.name:
                await bot.close()
                await bot.logout()
                exit(0)
            else:
                await ctx.channel.send(ctx.author.name + " you can't kill meme!")

        @bot.command(name="?")
        async def displayCommands(ctx): 
            await ctx.channel.send("""Commands for !Smayxor
Type !stock followed by Ticker DaysTillExpiry
Using !s Ticker will get you 0dte for that stock
Popular tickers just type  !spx   !spy !qqq !soxl !soxl !tqqq !sqqq !labu !tsla !aapl !amzn
Be sure to check the date stamp at the bottom of the images.  
A day will be added AH, and if no options are found 7-35 days may be added

The blue bars up top are Open Interest
The Red/Green bars above the strikes are Total Gamma, Red is Negative, Green is Positive
Below the strikes is Call Gamma and Put Gamma individually

!flist to display a list of fundamentals you can grab
!f Ticker FundamentalName   Will get you that fundamental
!fundamentals Ticker  Will get you ALL the fundamentals as a text file
!8ball or !8 Your question, with a ? at the end
!gm Posts GM image""")
        @bot.command(name="stock")
        async def stockChart(ctx, arg1, arg2):
            if ctx.author == bot.user: return
            
            ticky = arg1.upper()
            stock_price(arg1, arg2)
            with open('./stock-chart.png', 'rb') as fp: 
                await ctx.channel.send(file=discord.File(fp, 'stock-chart.png'))
        @bot.command(name="s")
        async def stockChart2(ctx, arg1): await stockChart(ctx, arg1, 0)
        @bot.command(name="spx")
        async def spxChart(ctx): await stockChart(ctx, "spx", 0)
        @bot.command(name="spy")
        async def spyChart(ctx): await stockChart(ctx, "spy", 0)
        @bot.command(name="qqq")
        async def qqqChart(ctx): await stockChart(ctx, "qqq", 0)
        @bot.command(name="soxl")
        async def soxlChart(ctx): await stockChart(ctx, "soxl", 7)
        @bot.command(name="soxs")
        async def soxsChart(ctx): await stockChart(ctx, "soxs", 7)
        @bot.command(name="tqqq")
        async def tqqqChart(ctx): await stockChart(ctx, "tqqq", 7)
        @bot.command(name="sqqq")
        async def sqqqChart(ctx): await stockChart(ctx, "sqqq", 7)
        @bot.command(name="labu")
        async def labuChart(ctx): await stockChart(ctx, "labu", 7)
        @bot.command(name="tsla")
        async def tslaChart(ctx): await stockChart(ctx, "tsla", 7)
        @bot.command(name="aapl")
        async def aaplChart(ctx): await stockChart(ctx, "aapl", 7)
        @bot.command(name="amzn")
        async def amznChart(ctx): await stockChart(ctx, "amzn", 7)
        @bot.command(name="meta")
        async def metaChart(ctx): await stockChart(ctx, "meta", 7)
        @bot.command(name="gme")
        async def gmeChart(ctx): await stockChart(ctx, "gme", 7)
        @bot.command(name="bbby")
        async def bbbyChart(ctx): await stockChart(ctx, "bbby", 7)
        @bot.command(name="oxy")
        async def oxyChart(ctx): await stockChart(ctx, "oxy", 7)
        @bot.command(name="mo")
        async def moChart(ctx): await stockChart(ctx, "mo", 7)
        @bot.command(name="ups")
        async def upsChart(ctx): await stockChart(ctx, "ups", 7)
        @bot.command(name="xom")
        async def xomChart(ctx): await stockChart(ctx, "xom", 7)
        @bot.command(name="mstr")
        async def mstrChart(ctx): await stockChart(ctx, "mstr", 7)
        @bot.command(name="cat")
        async def catChart(ctx): await stockChart(ctx, "cat", 7)
        @bot.command(name="good")
        async def goodChart(ctx): await stockChart(ctx, "good", 7)
        @bot.command(name="rivn")
        async def rivnChart(ctx): await stockChart(ctx, "rivn", 7)
        @bot.command(name="mara")
        async def maraChart(ctx): await stockChart(ctx, "mara", 7)
        @bot.command(name="riot")
        async def riotChart(ctx): await stockChart(ctx, "riot", 7)
        @bot.command(name="roku")
        async def rokuChart(ctx): await stockChart(ctx, "roku", 7)
        @bot.command(name="pypl")
        async def pyplChart(ctx): await stockChart(ctx, "pypl", 7)
        @bot.command(name="intc")
        async def intcChart(ctx): await stockChart(ctx, "intc", 7)
        @bot.command(name="nio")
        async def nioChart(ctx): await stockChart(ctx, "nio", 7)
        @bot.command(name="dkng")
        async def dkngChart(ctx): await stockChart(ctx, "dkng", 7)
        @bot.command(name="faze")
        async def fazeChart(ctx): await stockChart(ctx, "faze", 7)
        @bot.command(name="ge")
        async def geChart(ctx): await stockChart(ctx, "ge", 7)
        @bot.command(name="aeo")
        async def aeoChart(ctx): await stockChart(ctx, "aeo", 7)
        @bot.command(name="grnd")
        async def grndChart(ctx): await stockChart(ctx, "grnd", 7)
        @bot.command(name="rblx")
        async def rblxChart(ctx): await stockChart(ctx, "rblx", 7)
        @bot.command(name="msft")
        async def msftChart(ctx): await stockChart(ctx, "msft", 7)
        @bot.command(name="amc")
        async def amcChart(ctx): await stockChart(ctx, "amc", 7)
        @bot.command(name="wmt")
        async def wmtChart(ctx): await stockChart(ctx, "wmt", 7)
        @bot.command(name="crbl")
        async def crblChart(ctx): await stockChart(ctx, "crbl", 7)
        @bot.command(name="pltr")
        async def pltrChart(ctx): await stockChart(ctx, "pltr", 7)
        @bot.command(name="afrm")
        async def afrmChart(ctx): await stockChart(ctx, "afrm", 7)
        @bot.command(name="dltr")
        async def dltrChart(ctx): await stockChart(ctx, "dltr", 7)
        @bot.command(name="dg")
        async def dgChart(ctx): await stockChart(ctx, "dg", 7)
        @bot.command(name="etsy")
        async def etsyChart(ctx): await stockChart(ctx, "etsy", 7)
        @bot.command(name="snow")
        async def snowChart(ctx): await stockChart(ctx, "snow", 7)
        @bot.command(name="nflx")
        async def nflxChart(ctx): await stockChart(ctx, "nflx", 7)
        @bot.command(name="amd")
        async def amdChart(ctx): await stockChart(ctx, "amd", 7)
        @bot.command(name="f")
        async def fChart(ctx): await stockChart(ctx, "f", 7)
        @bot.command(name="dis")
        async def disChart(ctx): await stockChart(ctx, "dis", 7)
        @bot.command(name="ba")
        async def baChart(ctx): await stockChart(ctx, "ba", 7)
        
        bot.run(BOT_TOKEN)
        
""" Notes on Accounting
    P/E Ratio determines if company is over/under valued.  PE Ratio of 15 means current value of company is equal to 15 times its annual earnings.
    Lower P/E ratio is good, if you think it should be higher

    PEG Ratio price earnings to growth.  Target ratio below 1.0

    Quick Ratio = company liquidity, ability to pay bills.  higher ratio is better.   If its really high the company isnt using assests well

    ROE Return on Equity.   higher ROE is better.  use to compare similar companies.

    ROA Return on Assets.   better than ROE.  differs alot in dif industries

    DebtToEquity Ratio.   Higher ratio = more risk    well established companies can have a higher ratio

    FreeCashFlow shows how much money a company has to burn

    Price-to-Book Ratio P/B.   Value investors wants under 1.
"""

def rateFundamental(ticker_name, fundamental, value):
    rating = 5
    try:
        if 'Beta' in fundamental:
            rating = value * 4
            if rating > 9 : rating = 9
        elif 'DivYield' in fundamental:
            rating = 5 - value
        elif 'DivAmount' in fundamental:
            rating = 5 - value
        elif 'peRatio' in fundamental:
            rating = 10 - (1 / value)
        elif 'pegRatio' in fundamental:
            rating = (1 - value) * 10
        elif 'QuickRatio' in fundamental:
            rating = 100 / value
        elif 'DebtToCapital' in fundamental:
            rating = 5
        elif 'MarketCap' in fundamental:
            rating = int(value / 100000) 
        elif 'Calls' in fundamental:
            rating = 9
        elif 'Puts' in fundamental:
            rating = 0
        elif 'Total' in fundamental:
            total = CallDollars - PutDollars
            rating = 9 if total > (CallDollars * 0.25) else 0 if abs(total) > (PutDollars * 0.25) else 5
        elif 'VIX' in fundamental:
            rating = (float(value) - 10) / 2 
        elif 'Data' in value:
            rating = 0 if "Delayed" in fundamental else 9
    except:
        rating = 5
    if rating < 0: rating = 0
    if rating > 9: rating = 9
    if (ticker_name in fundamental) or ("DTE" in str(value)): color = "#0FF"
    else: color = colorGradient[int(rating)]
    return color

def drawRect(x, y, w, h, color, border):
    if border in 'none': border = color
#    if guiMode : canvas.create_rectangle(x, y, w, h, fill=color, outline=border)
    draw.rectangle([x,y,w,h], fill=color, outline=border)   #for PIL Image

def drawPriceLine(x, color):  #Draws a dashed line
#    if guiMode : canvas.create_line(x, 100, x, 350, dash=(4, 2), fill=color, width = 1)
    y = 100
    while y < 350:
        draw.line([x, y, x, y + 4], fill=color, width=1)
        y += 6

def drawText(x, y, txt, color):
    #text_width = font.getlength(txt)
#    if guiMode : canvas.create_text(x, y, anchor=NW, font=("Purisa", STR_FONT_SIZE), text=txt, fill=color)
    draw.text((x,y), text=txt, fill=color, font=font) 

def drawRotatedText(x, y, txt, color):  

    text_layer = PILImg.new('L', (100, FONT_SIZE))
    dtxt = ImageDraw.Draw(text_layer)
    dtxt.text( (0, 0), txt, fill=255, font=font)
    rotated_text_layer = text_layer.rotate(270.0, expand=1)
    
    PILImg.Image.paste( img, rotated_text_layer, (x,210) ) 
    #img.Image.paste( ImageOps.colorize(rotated_text_layer, (x,y,50), (90, 90,90)), rotated_text_layer, (x,200) ) 
    #    img.paste( ImageOps.colorize(rotated_text_layer, (x,y,50), (90, 90,90)), (42,60),  rotated_text_layer)
    #img.show()
    #Image.new("RGB", (IMG_W, IMG_H), "#000")
def daysFromNow(days):
    delta = dt.strptime(days.split(":")[0], "%Y-%m-%d") - dn
    return delta.days + 1

def clearScreen():
    #if guiMode : canvas.delete('all')
    drawRect(0,0,IMG_W,IMG_H, color="#000", border="#000")

def getFundamentals(ticker_name):
    page = requests.get(url=fundamental_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name))
    content = json.loads(page.content)[ticker_name]["fundamental"]
    result = {'Beta': content["beta"], 'DivYield': content["dividendYield"], 'DivDate': content["dividendDate"], 'DivAmount': content["dividendAmount"], 'peRatio': content["peRatio"], 'pegRatio': content["pegRatio"], 'QuickRatio': content["quickRatio"], 'DebtToCapital': content["totalDebtToCapital"], 'SharesOut': f'{int(content["sharesOutstanding"]):,}', 'Float': f'{(int(content["marketCapFloat"]) * 1000000):,}', 'MCap': f'{(int(content["marketCap"]) * 1000000):,}'}
    
#  "''revenueGrowth', 'operatingMargins', 'ebitda', 'targetLowPrice', 'grossProfits', 'freeCashflow', 'targetMedianPrice', 'currentPrice', 'earningsGrowth', 'currentRatio', 'returnOnAssets', 'targetMeanPrice', 'debtToEquity', 'returnOnEquity', 'targetHighPrice', 'totalCash', 'totalDebt', 'totalRevenue', 'totalCashPerShare', 'revenuePerShare', 'quickRatio','morningStarRiskRating', 'forwardEps', 'revenueQuarterlyGrowth', 'sharesOutstanding', 'fundInceptionDate', 'annualReportExpenseRatio', 'totalAssets', 'bookValue', 'sharesShort', 'sharesPercentSharesOut', 'fundFamily', 'lastFiscalYearEnd', 'heldPercentInstitutions', 'netIncomeToCommon', 'trailingEps', 'lastDividendValue', 'SandP52WeekChange', 'priceToBook', 'heldPercentInsiders', 'nextFiscalYearEnd', 'yield', 'mostRecentQuarter', 'shortRatio', 'sharesShortPreviousMonthDate', 'floatShares', 'beta', 'enterpriseValue', 'priceHint', 'threeYearAverageReturn', 'lastDividendDate', 'morningStarOverallRating', 'earningsQuarterlyGrowth', 'priceToSalesTrailing12Months', 'dateShortInterest', 'pegRatio', 'ytdReturn', 'forwardPE', 'lastCapGain', 'shortPercentOfFloat', 'sharesShortPriorMonth', 'impliedSharesOutstanding', 'fiveYearAverageReturn', 'twoHundredDayAverage', 'trailingAnnualDividendYield', 'payoutRatio', 'regularMarketDayHigh', 'navPrice', 'averageDailyVolume10Day', 'regularMarketPreviousClose', 'trailingAnnualDividendRate', 'dividendRate', 'exDividendDate', 'trailingPE', 'marketCap','dividendYield'"  
#    funds = yf.Ticker(ticker_name)
#    dict = funds.info
#    result = {'Beta': dict["beta"], 'DivYield': dict["dividendYield"], 'DivDate': dict["exDividendDate"], 'forwardPE': dict["forwardPE"], 'pegRatio': dict["pegRatio"], 'QuickRatio': dict["quickRatio"]}
    return result
    
def addStrike(strike, volume, oi, delta, gamma, vega, price, volatility, call, itm, bid, days):
    global ExpectedMove, GEX, DEX, VEX, Volas, OIS, CallDollars, PutDollars, atmDif, closestStrike
    try:
        if not strike in GEX: newStrike(strike)  #Prevents NaN values?
        if (oi == 0): return   #Delta and Gamma show up as -999.0
        if (delta > 990) or (delta < -990) : return #might only happen when OI is 0
        
        GEX[strike] += (gamma * oi * call)
        DEX[strike] += (delta * oi)
        VEX[strike] = vega
        Volas[strike] = volatility
        
        if (call == 1):
            CallGEX[strike] += (gamma * oi)
            CallDollars += (bid * oi)
        else:
            PutGEX[strike] += (gamma * oi)
            PutDollars += (bid * oi)
#        if (itm): OIS[strike] += oi
        OIS[strike] += oi

        distToMoney = (abs(strike - price))
        if distToMoney < atmDif: 
            atmDif = distToMoney
            closestStrike = strike
            ExpectedMove = volatility * math.sqrt(days / 365)
#        em = 0
#        if abs(strike - price) < 1.0 : em = volatility * math.sqrt(days / 365)
#        if em > ExpectedMove: ExpectedMove = em   #Each date should land on this strike, keep the biggest one
    except:
#        print("error")
        a=1

def newStrike(strike):
    global GEX, DEX, VEX, Volas, OIS
    GEX[strike] = 0
    CallGEX[strike] = 0
    PutGEX[strike] = 0
    DEX[strike] = 0
    VEX[strike] = 0
    Volas[strike] = 0
    OIS[strike] = 0

def clearArrays():
    global ExpectedMove, GEX, DEX, VEX, Volas, OIS, CallDollars, PutDollars, atmDif, closestStrike
    GEX.clear()
    CallGEX.clear()
    PutGEX.clear()
    DEX.clear()
    VEX.clear()
    Volas.clear()
    OIS.clear()
    ExpectedMove = 0.0
    CallDollars = 0.0
    PutDollars = 0.0
    atmDif = 999
    closestStrike = 0

def drawCharts(ticker_name, dte, price, delayed):
    global ExpectedMove, GEX, DEX, VEX, Volas, OIS, CallDollars, PutDollars, FONT_SIZE, closestStrike
#Get max GEX/DEX for math to draw chart,  alternative would be to make a'MAX' key in each array
    maxOIS = 0
    maxGEX = 0
    maxDEX = 0
    maxCPGEX = 0
    for strikes in GEX:
        if abs(GEX[strikes]) > maxGEX: maxGEX = abs(GEX[strikes])
        if abs(CallGEX[strikes]) > maxCPGEX: maxCPGEX = abs(CallGEX[strikes])
        if abs(PutGEX[strikes]) > maxCPGEX: maxCPGEX = abs(PutGEX[strikes])
        if abs(DEX[strikes]) > maxDEX: maxDEX = abs(DEX[strikes])
        if abs(OIS[strikes]) > maxOIS: maxOIS = abs(OIS[strikes])

#Draw the chart
    clearScreen()    
    x = -15
    for strikes in sorted(GEX):
        x += FONT_SIZE - 3
        txtColor = ("#0FF" if (x % 10 == 0) else "#3F3")  #just to make strikes stand out and not blur together
        """  Draws differently in PIL Image from TKinter Canvas, font size issues 
        upperPrice = int(strikes)
        lowerPrice = int((strikes % 1) * 100)
        strUpperPrice = str(upperPrice)
        strLowerPrice = str(lowerPrice)
        drawText(x, 205, txt=('\n'.join(strUpperPrice)), color=txtColor)
        if (lowerPrice > 0) :
            txtY = 205 + ((len(strUpperPrice) - 1) * FONT_SIZE)
            drawText(x + 5, txtY + 10, txt=".", color=txtColor)
            drawText(x, txtY + FONT_SIZE + 5, txt=('\n'.join(strLowerPrice)), color=txtColor)
        """
        drawRotatedText(x=x - 5, y=205, txt=str(strikes).replace('.0', ''), color=txtColor)
        #drawText(x, 205, txt=('\n'.join(str(strikes).replace('.0', ''))), color=txtColor)
        if (OIS[strikes] != 0): drawRect(x, 0, x + 12, ((abs(OIS[strikes]) / maxOIS) * 50), color="#00f", border='')
        if (GEX[strikes] != 0): drawRect(x, 205 - ((abs(GEX[strikes]) / maxGEX) * 150), x + 12, 205, color=("#0f0" if (GEX[strikes] > -1) else "#f00"), border='')
        if (DEX[strikes] != 0): drawRect(x, 205 - ((abs(DEX[strikes]) / maxDEX) * 150), x + 2, 205, color=("#077" if (DEX[strikes] > -1) else "#f77"), border='')
        if (CallGEX[strikes] != 0): drawRect(x, 389 - ((CallGEX[strikes] / maxCPGEX) * 100), x + 12, 389, color="#0f0", border='')
        if (PutGEX[strikes] != 0): drawRect(x, 391 + ((PutGEX[strikes] / maxCPGEX) * 100), x + 12, 391, color="#f00", border='')

        if float(strikes) == closestStrike:
            if price > closestStrike : drawPriceLine(x + 10, "#FF0")
            else : drawPriceLine(x, "#FF0")
            
#    fundamentals = getFundamentals(ticker_name)
    vix = json.loads(requests.get(url=vix_endpoint.format(api_key=MY_API_KEY)).content)['$VIX.X']['lastPrice']
    fundamentals = {}
    fundamentals[ticker_name] = "$" + str(price)
    fundamentals['VIX'] = "{:,.2f}".format(vix)
    fundamentals['ExpectedMove'] = str(round(ExpectedMove, 2)) + "%"
    fundamentals['EM'] = "${:,.2f}".format(price * (ExpectedMove / 100))
    fundamentals['Calls'] = "${:,.2f}".format(CallDollars)
    fundamentals['Puts'] = "${:,.2f}".format(PutDollars)
    fundamentals['Total'] = "${:,.2f}".format(CallDollars - PutDollars)
    fundamentals = {**fundamentals, **getFundamentals(ticker_name)}
    fundamentals["Delayed" if delayed else "Live"] = 'Data'    #Not needed as OAUTH code currently forces the issue, just showing off
    fundamentals[dte] = "DTE"
#    fundamentals = {ticker_name: "$" + str(price), **fundamentals}
    x = IMG_W - 250
    drawRect(x, 0, IMG_W, IMG_H, color="#000", border="#777")
    #drawRect(x+20, 30, x + 24, 500, color='#777', border='#333')
    x += 4
    y = 5
    for keys in fundamentals:
        drawText(x, y, txt=keys + ": " + str(fundamentals[keys]), color= str(rateFundamental(ticker_name, keys, fundamentals[keys])) )
        y += FONT_SIZE
    
#    drawText(0, 0, txt=str(ticker_name + ": $" + str(round(price, 2)) + " VIX " + str(vix) + " Expected Move " + str(round(ExpectedMove, 2)) + "% $" + str(round(price * (ExpectedMove / 100), 2))), color="#0FF")

    #drawText(0,470, txt=str(dte), color="#0ff")

    
def stock_price(ticker_name, days):
    global ExpectedMove, GEX, DEX, VEX, Volas, OIS, img, draw
    clearArrays()
    ticker_name = ticker_name.upper()

#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
    today = date.today()
    if "SPX" in ticker_name: ticker_name = "$SPX.X"
    if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours
#Force method to return results if DateRange is too small for stock to have options.  increment days until it works    
 #symbol': '$SPX.X', 'status': 'SUCCESS', 'underlying': None, 'strategy': 'SINGLE', 'interval': 0.0, 'isDelayed': True, 'isIndex': True, 'interestRate': 4.779, 'underlyingPrice': 4071.7, 'volatility': 29.0, 'daysToExpiration': 0.0, 'numberOfContracts': 80 'putExpDateMap' and 'callExpDateMap'
    loopAgain = True
    errorCounter = 0
    while loopAgain:
        dateRange = today + datetime.timedelta(days=int(days))
        content = json.loads(requests.get(url=options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', toDate=dateRange), headers=HEADER).content)
        if 'error' in content:  #happens when oauth token expires
            refreshTokens()
            errorCounter += 1
            if errorCounter == 5: break
        else:   
            if (content['status'] in 'FAILED'):   #happens when stock has no options, or stock doesnt exist
                days = str( int(days) + 7)
                loopAgain = int(days) < 37
            else: loopAgain = False
    #print('IsDelayed ', content['isDelayed'])
            
    if (content['status'] in 'FAILED') or (errorCounter == 5): #Failed, we tried our best
        clearScreen()
        drawText(0,0,txt="Failed to get data", color="#FF0")
        if serverMode : img.save("stock-chart.png")
        return
    price = content['underlyingPrice']   #underlyingprice == 0.0  same as   status == FAILED

    """  #Declaration For using pandas/numpy code.
    dataColumns ={'ExpirationDate':'','Calls':'1','LastSale':'0','Net':'0','Bid':'0','Ask':'0','Vol':'0','IV':'0','Delta':'0','Gamma':'0','OpenInt':'0','StrikePrice':'0'}
    df = pd.DataFrame(columns=dataColumns) """
#Load the data from JSON
    for days in content['callExpDateMap']: 
        for strikes in content['callExpDateMap'][days]:
            def addData(opts): addStrike(strike=opts["strikePrice"], volume=opts["totalVolume"], oi=opts["openInterest"], delta=opts['delta'], gamma=opts["gamma"], vega=opts['vega'], volatility=opts['volatility'], price=price, call=(1 if (opts['putCall'] in "CALL") else -1), itm=opts['inTheMoney'], bid=opts['bid'], days=daysFromNow(days))
            for options in content['callExpDateMap'][days][strikes]: addData(options)
            for options in content['putExpDateMap'][days][strikes]: addData(options)

#************* Paste pandas/numpy code here ****************
    
    drawCharts(ticker_name=ticker_name, dte=days, price=price, delayed=content['isDelayed'])
    
    #experimental search for Zero Gamma
    total_gamma = 0
    for strikes in GEX:
        total_gamma += GEX[strikes]
    total_gamma = total_gamma / price
    
    #Vanna Rally signals
    #Falling VIX
    #Crumbing IV
    #Larger than 'normal' retail PUT OI
    #if serverMode : 
    img.save("stock-chart.png")

    if guiMode:
        copyImg = PhotoImage(file="stock-chart.png")
        canvas.create_image(IMG_W_2, IMG_H_2, image=copyImg)
    
def gui_click_fetch():
    stock_price(ticker_name=e1.get(), days=e2.get())
    
def gui_click_loop():
    looper.start()

#Unused.  Draws a price chart
def thread_price_history(ticker):
    full_url = history_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    
    while True:
        page = requests.get(url=full_url)
        content = json.loads(page.content)
#{"candles": [{"open": 136.39,"high": 136.47,"low": 135.45,"close": 135.47,"volume": 276577,"datetime": 1667822400000}],"symbol": "AAPL","empty": false}    

        print(content)

        if content['empty']: break
        clearScreen()
        drawText(0,0,txt=content['symbol'],color="#00F")
        highs = []
        lows = []
        volumes = []
        times = []
        colors = []
        lowest = 9999.9
        highest = 0.0
        mostVol = 0.0
        startTime = 0
        for candles in content['candles']:     
            highs.append( candles['high'] )
            lows.append( candles['low'] )
            colors.append( "#F00" if (candles['open'] > candles['close']) else "#0F0" ) #open/close determines candle red/green
            volumes.append( candles['volume'] )
            times.append( candles['datetime'] )

            if candles['high'] > highest: highest = candles['high']# get max values, so we can trim it and scale to fit screen
            if candles['low'] < lowest: lowest = candles['low']   
            if candles['volume'] > mostVol: mostVol = candles['volume']
            if startTime == 0.0: startTime = candles['datetime']
            if candles['volume'] < 0: print("Negative ", candles['volume'])
        dif = abs(highest - lowest)  #amount to trim off of all values
        for i in range(len(highs)):  #scale numbers to fit on screen
            highs[i] = (((highest - highs[i]) / dif) * 400) + 30
            lows[i] = (((highest - lows[i]) / dif) * 400)  + 30
            volumes[i] = 495 - ((volumes[i] / mostVol) * 90)
        for i in range(len(highs)):
            x = i * 2
            canvas.create_line(x, highs[i], x, lows[i], fill=colors[i], width=2)
            canvas.create_line(x, volumes[i], x, 495, fill=colors[i], width=2)
        break 
    
def thread_price(ticker):
    full_url = price_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    
    while True:
        page = requests.get(url=full_url)
        content = json.loads(page.content)
#{'SPY': {'assetType': 'ETF', 'assetMainType': 'EQUITY', 'cusip': '78462F103', 'assetSubType': 'ETF', 'symbol': 'SPY', 'description': 'SPDR S&P 500', 'bidPrice': 393.0, 'bidSize': 1000, 'bidId': 'H', 'askPrice': 393.02, 'askSize': 500, 'askId': 'Z', 'lastPrice': 393.0, 'lastSize': 100, 'lastId': 'D', 'openPrice': 392.94, 'highPrice': 395.64, 'lowPrice': 391.97, 'bidTick': ' ', 'closePrice': 393.83, 'netChange': -0.83, 'totalVolume': 45894070, 'quoteTimeInLong': 1670443602438, 'tradeTimeInLong': 1670443602329, 'mark': 393.0, 'exchange': 'p', 'exchangeName': 'PACIFIC', 'marginable': True, 'shortable': True, 'volatility': 0.014, 'digits': 2, '52WkHigh': 479.98, '52WkLow': 348.11, 'nAV': 0.0, 'peRatio': 0.0, 'divAmount': 6.1757, 'divYield': 1.57, 'divDate': '2022-09-16 00:00:00.000', 'securityStatus': 'Normal', 'regularMarketLastPrice': 393.0, 'regularMarketLastSize': 1, 'regularMarketNetChange': -0.83, 'regularMarketTradeTimeInLong': 1670443602329, 'netPercentChangeInDouble': -0.2108, 'markChangeInDouble': -0.83, 'markPercentChangeInDouble': -0.2107, 'regularMarketPercentChangeInDouble': -0.2108, 'delayed': True, 'realtimeEntitled': False}}   
        #content[ticker]
        break
 
#*************Main "constructor" for GUI, starts thread for Server ********************

if serverMode : 
    if guiMode:
        x = threading.Thread(target=thread_discord)
        x.start()
    else:
        thread_discord()
if guiMode : 
    win = Tk()
    win.geometry(str(IMG_W + 5) + "x" + str(IMG_H + 45))

    Label(win, text="Ticker", width=10).grid(row=0, column=0, sticky='W')

    e1 = Entry(win, width=8)
    e1.grid(row=0, column=0, sticky='E')
    e1.insert(0, ticker_name)

    e2 = Entry(win, width=4)
    e2.grid(row=0, column=1, sticky='E')
    e2.insert(0, '0')

    Label(win, text="Days", width=10).grid(row=0, column=2, sticky='W')
    Button(win, text="Fetch", command=gui_click_fetch, width=5).grid(row=0, column=2, sticky='E')
    Button(win, text="Loop", command=gui_click_loop, width=5).grid(row=0, column=3, sticky='N')

    canvas = Canvas(win, width=IMG_W, height=IMG_H)
    canvas.grid(row=4, column=0, columnspan=20, rowspan=20)
    canvas.configure(bg="#000000")

    stock_price(ticker_name, 0)
    looper = threading.Thread(target=thread_price, args=(e1.get(),))
    mainloop()
    #serverSockThread.join()
    if serverMode :
        #x.shutdown(wait=True)
        print("Killing bot")
#        bot.command(name = "!kill")  #*********Needs some work still**********can be closed from inside discord 
        #x.join()
    
        print("Bot dead?")
    looper.join()
#if serverMode : os.remove("stock-chart.png", dir_fd=None)
#print("End of program")




"""
#Block comment for all the pandas/numpy code.   Might require Put-Call specific fields for later compatability 
def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21

# Black-Scholes European-Options Gamma
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    if T == 0 or vol == 0:
        return 0

    dp = (np.log(S/K) + (r - q + 0.5*vol**2)*T) / (vol*np.sqrt(T))
    dm = dp - vol*np.sqrt(T) 

    if optType == '1':
        gamma = np.exp(-q*T) * norm.pdf(dp) / (S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 
    else: # Gamma is same for calls and puts. This is just to cross-check
        gamma = K * np.exp(-r*T) * norm.pdf(dm) / (S * S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 
        
        

#**********Starting in code section to parse JSON
            for options in content['callExpDateMap'][days][strikes]:
                dataRow = [days.split(":")[0], '1', '0', '0', options['bid'], options['ask'], options['totalVolume'], options['volatility'], options['delta'], options['gamma'], options['openInterest'], strikes]
                df.loc[len(df.index)] = dataRow
            for options in content['putExpDateMap'][days][strikes]:
                dataRow = [days.split(":")[0], '-1', '0', '0', options['bid'], options['ask'], options['totalVolume'], options['volatility'], options['delta'], options['gamma'], options['openInterest'], strikes]
                df.loc[len(df.index)] = dataRow


    df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], format='%Y-%m-%d')
    df['ExpirationDate'] = df['ExpirationDate'] + datetime.timedelta(hours=16)
    df['StrikePrice'] = df['StrikePrice'].astype(float)
    df['IV'] = df['IV'].astype(float)
    df['Gamma'] = df['Gamma'].astype(float)
    df['OpenInt'] = df['OpenInt'].astype(float)
    df['Calls'] = df['Calls'].astype(float)



    fromStrike = 0.8 * price
    toStrike = 1.2 * price

# ---=== CALCULATE SPOT GAMMA ===---
# Gamma Exposure = Unit Gamma * Open Interest * Contract Size * Spot Price 
# To further convert into 'per 1% move' quantity, multiply by 1% of spotPrice
    df['GEX'] = df['Gamma'] * df['OpenInt'] * 100 * price * price * 0.01 * df['Calls']


    df['TotalGamma'] = df.GEX / 10**9
    dfAgg = df.groupby(['StrikePrice']).sum(numeric_only=True)
    strikes = dfAgg.index.values

    # Chart 1: Absolute Gamma Exposure
#    plt.grid()
#    plt.bar(strikes, dfAgg['TotalGamma'].to_numpy(), width=6, linewidth=0.1, edgecolor='k', label="Gamma Exposure")
#    plt.xlim([fromStrike, toStrike])
#    chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum())) + " Bn per 1% SPX Move"
#    plt.title(chartTitle, fontweight="bold", fontsize=20)
#    plt.xlabel('Strike', fontweight="bold")
#    plt.ylabel('Spot Gamma Exposure ($ billions/1% move)', fontweight="bold")
#    plt.axvline(x=price, color='r', lw=1, label="SPX Spot: " + str("{:,.0f}".format(price)))
#    plt.legend()
#    plt.show()

# ---=== CALCULATE GAMMA PROFILE ===---
    levels = np.linspace(fromStrike, toStrike, 60)

    # For 0DTE options, I'm setting DTE = 1 day, otherwise they get excluded
    df['daysTillExp'] = [1/262 if (np.busday_count(today, x.date())) == 0 \
                               else np.busday_count(today, x.date())/262 for x in df.ExpirationDate]

    nextExpiry = df['ExpirationDate'].min()

    df['IsThirdFriday'] = [isThirdFriday(x) for x in df.ExpirationDate]
    thirdFridays = df.loc[df['IsThirdFriday'] == True]
    nextMonthlyExp = thirdFridays['ExpirationDate'].min()

    totalGamma = []
    totalGammaExNext = []
    totalGammaExFri = []
# For each spot level, calc gamma exposure at that point
    for level in levels:
        df['GammaEx'] = df.apply(lambda row : calcGammaEx(level, row['StrikePrice'], row['IV'], 
                                                              row['daysTillExp'], 0, 0, "Calls", row['OpenInt']), axis = 1)
        totalGamma.append(df['GammaEx'].sum() * df['Calls'])
        exNxt = df.loc[df['ExpirationDate'] != nextExpiry]
        totalGammaExNext.append(exNxt['GammaEx'].sum() * exNxt['Calls'].sum())

        exFri = df.loc[df['ExpirationDate'] != nextMonthlyExp]
        totalGammaExFri.append(exFri['GammaEx'].sum() * exFri['Calls'].sum())


    totalGamma = np.array(totalGamma) / 10**9
    totalGammaExNext = np.array(totalGammaExNext) / 10**9
    totalGammaExFri = np.array(totalGammaExFri) / 10**9

    # Find Gamma Flip Point
    zeroCrossIdx = np.where(np.diff(np.sign(totalGamma)))[0]

    negGamma = totalGamma[zeroCrossIdx]
    posGamma = totalGamma[zeroCrossIdx+1]    #current section causing bug, index out of bounds
    negStrike = levels[zeroCrossIdx]
    posStrike = levels[zeroCrossIdx+1]

    # Writing and sharing this code is only possible with your support! 
    # If you find it useful, consider supporting us at perfiliev.com/support :)
    zeroGamma = posStrike - ((posStrike - negStrike) * posGamma/(posGamma-negGamma))
    zeroGamma = zeroGamma[0]

    print(df)
    print(zeroGamma)
"""
