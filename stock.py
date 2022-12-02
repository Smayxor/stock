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

import yfinance as yf
#import pandas as pd
#import numpy as np
#import scipy
#from scipy.stats import norm
#import matplotlib.pyplot as plt

#To make run on an Android phone, install app Pydroid and pip install discord.py requests colour.   Turn OFF battery saver features so apps arent being put to sleep.  Can also Enabled Developer Mode and enable Keep Phone Screen On While Charging
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
options_endpoint = "https://api.tdameritrade.com/v1/marketdata/chains?apikey={api_key}&symbol={stock_ticker}&contractType=ALL&strikeCount={count}&range=NTM&fromDate={fromDate}&toDate={toDate}&optionType=ALL"
fundamental_endpoint = "https://api.tdameritrade.com/v1/instruments?apikey={api_key}&symbol={stock_ticker}&projection=fundamental"

IMG_W = 1000
IMG_H = 500
ticker_name = 'SPY'
GEX = {}
DEX = {}
VEX = {}
Volas = {}
Pain = {}
CallGEX = {}
PutGEX = {}
ExpectedMove = 0.0
dn = datetime.datetime.now()
dn = dn.replace(hour=0, minute=0, second=0, microsecond=0)

#Generate a color gradient between red and green, used to rate fundamentals and look cool doing it
red = Color("#FF0000")
colorGradient = list(red.range_to(Color("#00FF00"),10))
colorGradient[0] = "#FF0000"
colorGradient[9] = "#00FF00"

serverMode = True
guiMode = False
n = len(sys.argv)
if (n > 1) :
    serverMode = sys.argv[1] in "server"
    guiMode = sys.argv[1] in "gui"
print("ServerMode/GUIMode", serverMode, guiMode)

if guiMode: from tkinter import *
if serverMode:
    from PIL import Image, ImageDraw, ImageGrab, ImageFont
    import discord
    from discord.ext import commands
    #************************************************************
    #Windows should just find the font file in its path.  Linux you can specify a path to font, or copy the .ttf to same folder
    font = ImageFont.truetype("Arimo-Regular.ttf", 28, encoding="unic")   
    #************************************************************

    #DISCORD_PERMISSIONS = 274877942784
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='!', intents=intents)
    def thread_discord():
        listOfKeys = "'fullTimeEmployees', 'longBusinessSummary', 'ebitdaMargins', 'profitMargins', 'grossMargins', 'operatingCashflow', 'revenueGrowth', 'operatingMargins', 'ebitda', 'targetLowPrice', 'grossProfits', 'freeCashflow', 'targetMedianPrice', 'currentPrice', 'earningsGrowth', 'currentRatio', 'returnOnAssets', 'targetMeanPrice', 'debtToEquity', 'returnOnEquity', 'targetHighPrice', 'totalCash', 'totalDebt', 'totalRevenue', 'totalCashPerShare', 'revenuePerShare', 'quickRatio', 'recommendationMean', 'annualHoldingsTurnover', 'enterpriseToRevenue', 'beta3Year', 'enterpriseToEbitda', '52WeekChange', 'morningStarRiskRating', 'forwardEps', 'revenueQuarterlyGrowth', 'sharesOutstanding', 'fundInceptionDate', 'annualReportExpenseRatio', 'totalAssets', 'bookValue', 'sharesShort', 'sharesPercentSharesOut', 'fundFamily', 'lastFiscalYearEnd', 'heldPercentInstitutions', 'netIncomeToCommon', 'trailingEps', 'lastDividendValue', 'SandP52WeekChange', 'priceToBook', 'heldPercentInsiders', 'nextFiscalYearEnd', 'yield', 'mostRecentQuarter', 'shortRatio', 'sharesShortPreviousMonthDate', 'floatShares', 'beta', 'enterpriseValue', 'priceHint', 'threeYearAverageReturn', 'lastDividendDate', 'morningStarOverallRating', 'earningsQuarterlyGrowth', 'priceToSalesTrailing12Months', 'dateShortInterest', 'pegRatio', 'ytdReturn', 'forwardPE', 'lastCapGain', 'shortPercentOfFloat', 'sharesShortPriorMonth', 'impliedSharesOutstanding', 'fiveYearAverageReturn', 'twoHundredDayAverage', 'trailingAnnualDividendYield', 'payoutRatio', 'regularMarketDayHigh', 'navPrice', 'averageDailyVolume10Day', 'regularMarketPreviousClose', 'trailingAnnualDividendRate', 'dividendRate', 'exDividendDate', 'trailingPE', 'marketCap','dividendYield'"
        @bot.command(name="f")
        async def stockChart(ctx, arg1, arg2):
            funds = yf.Ticker(arg1)
            dict = funds.info
#            print(dict.keys())
            #df = pd.DataFrame.from_dict(dict,orient='index')
            #df = df.reset_index()
            if arg2 in "list": 
                await ctx.channel.send(listOfKeys)
            else:
                await ctx.channel.send(arg1.upper() + " " + arg2 + " : " + str(dict[arg2]))

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
            await ctx.channel.send("Commands for !Smayxor \n Type !stock or !s   followed by Ticker DaysTillExpiry \n Popular tickers just type  !spx   !spy !qqq !soxl !soxl !tqqq !sqqq !labu !tsla !aapl !amzn")

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
        async def soxlChart(ctx): await stockChart(ctx, "soxl", 0)
        @bot.command(name="soxs")
        async def soxsChart(ctx): await stockChart(ctx, "soxs", 0)
        @bot.command(name="tqqq")
        async def tqqqChart(ctx): await stockChart(ctx, "tqqq", 0)
        @bot.command(name="sqqq")
        async def sqqqChart(ctx): await stockChart(ctx, "sqqq", 0)
        @bot.command(name="labu")
        async def labuChart(ctx): await stockChart(ctx, "labu", 0)
        @bot.command(name="tsla")
        async def tslaChart(ctx): await stockChart(ctx, "tsla", 0)
        @bot.command(name="aapl")
        async def aaplChart(ctx): await stockChart(ctx, "aapl", 0)
        @bot.command(name="amzn")
        async def amznChart(ctx): await stockChart(ctx, "amzn", 0)
        
        bot.run(BOT_TOKEN)

""" for logging in as a user.  not finished       
import discord
dc = DiscordClient()

class DiscordClient(discord.Client):
    def __init__(self, *args, **kwargs):
        discord.Client.__init__(self, **kwargs)

    @asyncio.coroutine
    def on_ready(self):
        servers = list(self.servers)
        for server in servers:
            if server.name == 'My server':
                break

        for channel in server.channels:
            if channel.name == 'general':
                break

        now = datetime.datetime.now()
        yield from self.send_message(channel, 'Api Success! at ' + str(now))
        print('Success!')
        yield from self.close()


if __name__ == '__main__':
    dc = DiscordClient()
    email = input('email : ')
    password = input('password : ')
    dc.run(email, password)
"""   
        
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

def rateFundamental(fundamental, value):
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
    except:
        rating = 5
    if rating < 0: rating = 0
    if rating > 9: rating = 9
    color = colorGradient[int(rating)]
    return color

def drawRect(x, y, w, h, color, border):
    if border in 'none': border = color
    if guiMode : canvas.create_rectangle(x, y, w, h, fill=color, outline=border)
    if serverMode : draw.rectangle([x,y,w,h], fill=color, outline=border)   #for PIL Image

def drawText(x, y, txt, color):
    #text_width = font.getlength(txt)
    if guiMode : canvas.create_text(x, y, anchor=NW, font="Purisa", text=txt, fill=color)
    if serverMode : draw.text((x,y), text=txt, fill=color, font=font)    
        
def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21

def daysFromNow(days):
    delta = dt.strptime(days.split(":")[0], "%Y-%m-%d") - dn
    return delta.days + 1
 
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

def addStrike(strike, volume, oi, delta, gamma, vega, price, volatility, call, itm, bid, days):
    global ExpectedMove, GEX, DEX, VEX, Volas, Pain
    try:
        if not strike in GEX:   #Prevents NaN values
            GEX[strike] = 0
            CallGEX[strike] = 0
            PutGEX[strike] = 0
            DEX[strike] = 0
            VEX[strike] = 0
            Volas[strike] = 0
            Pain[strike] = 0
        if (oi == 0): return   #Delta and Gamma show up as -999.0

        if (delta > 990) or (delta < -990) : print("Boom", strike, days, oi, delta, gamma, vega, volatility)

        GEX[strike] += (gamma * oi * call)
        DEX[strike] += (delta * oi)
        VEX[strike] = vega
        Volas[strike] = volatility

        if (call == 1):
            CallGEX[strike] += (gamma * oi)
#            if strike == 420: print(delta, gamma)
        else:
            PutGEX[strike] += (gamma * oi)
#            if strike == 420: print(delta, gamma)
        if (itm): Pain[strike] += oi
        
        em = 0
        if (strike - int(price)) == 0 : em = volatility * math.sqrt(days / 365)
        if em > ExpectedMove: ExpectedMove = em   #Each date should land on this strike, keep the biggest one
    except:
        a = 1

def gui_click_fetch():
    stock_price(ticker_name=e1.get().upper(), days=e2.get())

def stock_price(ticker_name, days):
    global ExpectedMove, GEX, DEX, VEX, Volas, Pain, img, draw
    GEX.clear()
    CallGEX.clear()
    PutGEX.clear()
    DEX.clear()
    VEX.clear()
    Volas.clear()
    Pain.clear()
    ExpectedMove = 0.0
    ticker_name = ticker_name.upper()

#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
    today = date.today()
    if "SPX" in ticker_name: ticker_name = "$SPX.X"          #        if guiMode:#            e1.delete(0, END)#            e1.insert(0, ticker_name)    #else:   #Don't increment day for SPX index, it only gives 0DTE option chain
    if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)   #ADJUST FOR YOUR TIMEZONE,  options data contains NaN after hours
    dateRange = today + datetime.timedelta(days=int(days))
#    print( ticker_name + " \ ", today, dateRange )

    full_url = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', fromDate=today, toDate=dateRange)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    price = content['underlyingPrice']




#******************* add better code to determine if a stock exists, or if option chain has data, and dte for next option



#Force method to return results if DateRange is too small for stock to have options.  increment days until it works     
    if (content['status'] in 'FAILED') and (int(days) < 30):
        days = str( int(days) + 1)
        stock_price(ticker_name, days)
        return

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

#Get max GEX/DEX for math to draw chart
    maxPain = 0
    maxGEX = 0
    maxDEX = 0
    maxCPGEX = 0
    for strikes in GEX:
        if abs(GEX[strikes]) > maxGEX: maxGEX = abs(GEX[strikes])
        if abs(CallGEX[strikes]) > maxCPGEX: maxCPGEX = abs(CallGEX[strikes])
        if abs(PutGEX[strikes]) > maxCPGEX: maxCPGEX = abs(PutGEX[strikes])
        if abs(DEX[strikes]) > maxDEX: maxDEX = abs(DEX[strikes])
        if abs(Pain[strikes]) > maxPain: maxPain = abs(Pain[strikes])
    
#Draw the chart
    if guiMode : canvas.delete('all')
    if serverMode : drawRect(0,0,IMG_W,IMG_H, color="#000", border="#000")
    
    x = -10
    for strikes in sorted(GEX):
        x += 15
        drawText(x, 235, txt=('\n'.join(str(strikes).replace('.0', ''))), color="#0F0")
        if (Pain[strikes] != 0): drawRect(x, 30, x + 9, 30 + ((abs(Pain[strikes]) / maxPain) * 50), color="#00f", border='')
        if (GEX[strikes] != 0): drawRect(x, 235 - ((abs(GEX[strikes]) / maxGEX) * 150), x + 9, 235, color=("#0f0" if (GEX[strikes] > -1) else "#f00"), border='')
        if (DEX[strikes] != 0): drawRect(x, 235 - ((abs(DEX[strikes]) / maxDEX) * 150), x + 2, 235, color=("#077" if (DEX[strikes] > -1) else "#f77"), border='')
        if (CallGEX[strikes] != 0): drawRect(x, 399 - ((CallGEX[strikes] / maxCPGEX) * 50), x + 9, 399, color="#0f0", border='')
        if (PutGEX[strikes] != 0): drawRect(x, 401 + ((PutGEX[strikes] / maxCPGEX) * 50), x + 9, 401, color="#f00", border='')

#experimental search for Zero Gamma
    total_gamma = 0
    for strikes in GEX:
        total_gamma += GEX[strikes]
    total_gamma = total_gamma / price
#    print('TotalGamma', total_gamma)
#    print(Pain)

#Get company fundamentals
    page = requests.get(url=fundamental_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name))
    content = json.loads(page.content)[ticker_name]["fundamental"]
    fundamentals = {'Beta': content["beta"], 'DivYield': content["dividendYield"], 'DivDate': content["dividendDate"], 'DivAmount': content["dividendAmount"], 'peRatio': content["peRatio"], 'pegRatio': content["pegRatio"], 'QuickRatio': content["quickRatio"], 'DebtToCapital': content["totalDebtToCapital"], 'SharesOutstanding': content["sharesOutstanding"], 'MarketCapFloat': content["marketCapFloat"], 'MarketCap': content["marketCap"], 'ShortInt': content["shortIntToFloat"], 'ShortDaysToCover': content["shortIntDayToCover"]}
    drawRect(x+20, 30, x + 24, 500, color='#777', border='#333')
    x += 27
    y = 28
    for keys in fundamentals:
        drawText(x, y, txt=keys + ": " + str(fundamentals[keys]), color= str(rateFundamental(keys, fundamentals[keys])) )
        y += 25

# For every 16 points of VIX expect 1% move on SPY
    drawText(0, 0, txt=str(ticker_name + ": $" + str(round(price, 2)) + " VIX " + str(json.loads(requests.get(url=vix_endpoint.format(api_key=MY_API_KEY)).content)['$VIX.X']['lastPrice']) + " Expected Move " + str(round(ExpectedMove, 2)) + "% $" + str(round(price * (ExpectedMove / 100), 2))), color="#0FF")

    drawText(0,470, txt=str(days) + "DTE", color="#0ff")

    if serverMode : img.save("stock-chart.png")
        
    
    
    
#Under construction.  plans to add 10min chart
def gui_click_loop():
#Get todays date, and hour.  Adjust date ranges so as not get data on a closed day
    today = date.today()
    if (int(time.strftime("%H")) > 12): today += datetime.timedelta(days=1)
    dateRange = today + datetime.timedelta(days=int(e2.get()))
    ticker_name = e1.get().upper()

    full_url = options_endpoint.format(api_key=MY_API_KEY, stock_ticker=ticker_name, count='40', fromDate=today, toDate=dateRange)
    page = requests.get(url=full_url)
    content = json.loads(page.content)
    price = content['underlyingPrice']




#*************Main "constructor" for GUI, starts thread for Server ********************
if serverMode : 
    img = Image.new("RGB", (IMG_W, IMG_H), "#000")
    draw = ImageDraw.Draw(img)
    if guiMode:
        x = threading.Thread(target=thread_discord)
        x.start()
    else:
        thread_discord()
    #print("Running")
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
    #print("Starting GUI")
    mainloop()
    #print("Ending GUI")
    if serverMode :
        #x.shutdown(wait=True)
        print("Killing bot")
#        bot.command(name = "!kill")  #*********Needs some work still**********can be closed from inside discord 
        x.join()
        print("Bot dead?")

#if serverMode : os.remove("stock-chart.png", dir_fd=None)
#print("End of program")





"""  #Block comment for all the pandas/numpy code.   Might require Put-Call specific fields for later compatability
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



"""

https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory?apikey={apikey}&periodType=day&period=10&frequencyType=minute&frequency=30&needExtendedHoursData=true"
{
  "candles": [
    {
      "open": 136.39,
      "high": 136.47,
      "low": 135.45,
      "close": 135.47,
      "volume": 276577,
      "datetime": 1667822400000
    }
  ],
  "symbol": "AAPL",
  "empty": false
}

https://api.tdameritrade.com/v1/marketdata/%24SPX.X/movers?apikey={apikey}&direction=down&change=percent
[broken]

https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes?apikey={apikey}
https://api.tdameritrade.com/v1/instruments?apikey={apikey}&symbol={ticker}&projection=fundamental

"""