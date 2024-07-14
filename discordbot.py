import datetime
import time
import ujson as json
import math
import threading
import sys
import random
from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands
from urllib.parse import unquote as unenc
from urllib.parse import quote as enc
import datapuller as dp
import drawchart as dc
import requests
import os

init = json.load(open('apikey.json'))
BOT_TOKEN = init['BOT_TOKEN']
BOT_APP_ID = init['DISCORD_APP_ID']
BOT_USER_FOR_KILL = init['BOT_KILL_USER']  #make it your discord user name
TENOR_API_KEY = init['TENOR_API_KEY']
UPDATE_CHANNEL = init['UPDATE_CHANNEL']    #Channel ID stored as Integer not string

WEEKDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
CHARTS_TEXT = ["GEX ", "GEX Volume ", "IV ", "DAILY IV ", "EGEX ", "COMBINED ", "ATR+FIB ", "LAST DTE ", "LOG-DATA ", "CHANGE IN GEX ", "SKEWED GEX ", "HEAT MAP "]
CHART_GEX = 0
CHART_VOLUME = 1
CHART_IV = 2
CHART_DAILYIV = 3
CHART_EGEX = 4
CHART_COMBO = 5
CHART_ATR = 6
CHART_LASTDTE = 7
CHART_LOG = 8
CHART_CHANGE = 9
CHART_SKEW = 10
CHART_HEATMAP = 11

try :
	#Declarations for slash commands
	url = "https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands"
	headers = { "Authorization": "Bot " + BOT_TOKEN}

	#Removes slash commands
	#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/COMMAND_ID", headers=headers) )
	#print( requests.delete("https://discord.com/api/v10/applications/" + BOT_APP_ID + "/commands/1260647680405930064", headers=headers) )

	slash_command_json = {
		"name": "gex", "type": 1, "integration_types": [0, 1], "contexts": [0,1,2], "description": "Draw a GEX/DEX chart", "options": [ 
		{ "name": "ticker", "description": "Stock Ticker Symbol", "type": 3, "required": True }, 
		{ "name": "dte", "description": "Days to expiration", "type": 4, "required": False }, 
		{ "name": "count", "description": "Strike Count", "type": 4, "required": False }, 
		{ "name": "chart", "description": "R for roated chart", "type": 3, "required": False, "choices": [
			{ "name": "Normal", "value": "Normal"  }, 
			{ "name": "EGEX", "value": "E" }, 
			{ "name": "Volume", "value": "V" }, 
			{ "name": "COMBO", "value": "COMBO"  }, 
			{ "name": "HEATMAP", "value": "HEATMAP"  }
		]}   
	] }
	print( requests.post(url, headers=headers, json=slash_command_json) )

	slash_command_json = { "name": "8ball", "type": 1, "integration_types": [0, 1], "contexts": [0,1,2], "description": "Answers your question", "options": [ { "name": "question", "description": "Question you need answered?", "type": 3, "required": True }] }
	print( requests.post(url, headers=headers, json=slash_command_json) )

	slash_command_json = { "name": "pc", "type": 1, "integration_types": [0, 1], "contexts": [0,1,2], "description": "Have Smayxor display price charts", "options":[
		{ "name": "strike1", "description": "5560c", "type": 3, "required": True }, 
		{ "name": "strike2", "description": "5560p", "type": 3, "required": False }] }
	print( requests.post(url, headers=headers, json=slash_command_json) )

	slash_command_json = { "name": "news", "type": 1, "integration_types": [0, 1], "contexts": [0,1,2], "description": "Gets todays events", "options":[{ "name": "days", "description": "How many days", "type": 3, "required": False, "choices": [{"name": "today", "value": "TODAY"}, {"name": "week", "value": "WEEK"}, {"name": "all", "value": "ALL"}, {"name": "1", "value": "1"}, {"name": "2", "value": "2"}, {"name": "3", "value": "3"}, {"name": "4", "value": "4"}, {"name": "5", "value": "5"}] }] }
	print( requests.post(url, headers=headers, json=slash_command_json) )

except Exception as er:
	print(f'SlashCommand Error - {er}')

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

def isThirdFriday(d):    return d.weekday() == 4 and 15 <= d.day <= 21

def get_expiry_date_for_month(curr_date):
    """
    http://cfe.cboe.com/products/spec_vix.aspx

    TERMINATION OF TRADING:

    Trading hours for expiring VIX futures contracts end at 7:00 a.m. Chicago
    time on the final settlement date.

    FINAL SETTLEMENT DATE:

    The Wednesday that is thirty days prior to the third Friday of the
    calendar month immediately following the month in which the contract
    expires ("Final Settlement Date"). If the third Friday of the month
    subsequent to expiration of the applicable VIX futures contract is a
    CBOE holiday, the Final Settlement Date for the contract shall be thirty
    days prior to the CBOE business day immediately preceding that Friday.
    """
    # Date of third friday of the following month
    if curr_date.month == 12:
        third_friday_next_month = datetime.date(curr_date.year + 1, 1, 15)
    else:
        third_friday_next_month = datetime.date(curr_date.year,
                                          curr_date.month + 1, 15)

    one_day = datetime.timedelta(days=1)
    thirty_days = datetime.timedelta(days=30)
    while third_friday_next_month.weekday() != 4:
        # Using += results in a timedelta object
        third_friday_next_month = third_friday_next_month + one_day

    # TODO: Incorporate check that it's a trading day, if so move the 3rd
    # Friday back by one day before subtracting
    return third_friday_next_month - thirty_days
	
	
	
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
		header = { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0",
            "Accept": "application/json, text/plain, */*", "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3" }
		data = requests.get(url=url, headers=header)
		
		text = ""
		tables = data.text.split( "<tbody>" )
		#print( tables )
		txt = tables[1].split("</tbody>")[0] + tables[2].split("</tbody>")[0]
		txt = txt.replace('<b>', '', 1).replace('<tr>','').replace('S&amp;P', '').replace('<td style="text-align: left;">', '').replace('\r', '').replace('\n', '').split('<b>')
		for t in txt:
			#print(t)
			t = t.replace('<td>', '').split('</tr>', 1)
			day = t[0].replace('</td>', '').replace('</b>', '').replace('. ', '.').replace('.', ' ')
			if ('FRIDAY' in day) and (15 <= int(day.split(' ')[2]) <= 21) : day = day.replace('FRIDAY', 'MOPEX - FRIDAY')
			newsD = NewsData( day )
			for r in t[1].split('</tr>'):
				event = ""
				counter = 0
				for td in r.split('</td>'):
					if counter == 0:
						if len(td) == 7 : td = td.replace(' ', '  ')
						event = td
					else:
						while (counter == 1) and (len(td) < 40): td = td + ' '	
						if len(td) > 0: event += COLUMN[counter] + td
					counter += 1
				newsD.addEvent( event )
			news.append( newsD )
	except Exception as er:
		print(f'BOOM {er}')
		#for x in news: print( x.toString() )
		#news.append( NewsData(today) )
	todaysNews = news
	return news

class MyNewHelp(commands.MinimalHelpCommand):
	async def send_pages(self):
		strHelp = """}help for commands for Smayxor
/gex ticker dte strike-count charttype
/8ball followed by a question, ending in ?
/news days <- Displays upcoming events

The blue bars on left are OI.
The Red/Green bars left of the strikes are Total Gamma Exposure.
To the right of the strikes is Call Put GEX individually

}gm }tits }ass }pump }dump also exist"""
		destination = self.get_destination()
		for page in self.paginator.pages:
			await destination.send(strHelp)
bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyNewHelp(), sync_commands=True)
def getChartType( arg ):
	arg = arg.upper()
	if arg == 'V': return CHART_VOLUME
	elif arg == 'IV': return CHART_IV
	elif arg == 'DAILYIV': return CHART_DAILYIV
	elif arg == 'E': return CHART_EGEX
	elif arg == 'COMBO': return CHART_COMBO
	elif arg == 'ATR': return CHART_ATR
	elif arg == 'LD': return CHART_LASTDTE
	elif arg == 'CHANGE': return CHART_CHANGE
	elif arg == 'SKEW': return CHART_SKEW
	elif arg == 'HEATMAP': return CHART_HEATMAP
	else: return CHART_GEX

def getStrTime(): 
	now = datetime.datetime.now()
	return (now.hour * 100) + now.minute + (now.second * 0.01)

#@app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)#(i.guild_id, i.user.id))
@bot.tree.command(name="gex", description="Draws a GEX chart")
async def slash_command_gex(intr: discord.Interaction, ticker: str = "SPY", dte: int = 0, count: int = 40, chart: str = "R"):
	global tickers, updateRunning, needsQueue
	perms = await checkInteractionPermissions( intr )
	if perms[1] > 0 :
		await intr.response.send_message(f'Using /gex has a 20 second cooldown - {perms[1]} seconds remaining', ephemeral=True)
		return
	"""
	minute = getStrTime()
	if 615 < minute < 630 and BOT_USER_FOR_KILL != str(intr.user) :
		randomMessage = ["Charting down for server maintenance during 15 minutes before Market Open.",
						"Bot is refreshing, go run one out, those are rookie numbers",
						"Smaybot is updating, please boost server for more info",
						"Go read Mark Douglas for a few"]
		await intr.response.send_message(random.choice(randomMessage), ephemeral=True)
		return"""
	await intr.response.defer(thinking=True, ephemeral=perms[3] == False)
	ticker = ticker.upper()
	chartType = getChartType( chart )
	if chartType == CHART_HEATMAP:
		fn = dc.drawWeeklyChart()
	else:
		fn = ""
		
		if chartType == CHART_COMBO:
			fn = grabFridayCombo(dte)
			
		elif "SPX." in ticker: # Pull the data from PC Server,  needs to check if server is even available
			try :
				tmp = ticker.split(".")
				ticker = tmp[0]
				minute = float(tmp[1])
				
				fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
				file = fileList[-1]
				gexData = dp.pullLogFile(file, discordBot=True)
				strikes = None
				dif = 99999

				for t in gexData:
					tmp = abs(float(t) - minute)
					if tmp < dif :
						dif = tmp
						strikes = gexData[t]
						dte = t
				fn = dc.drawGEXChart("SPX", 30, dte=0, strikes=strikes, expDate=dte)
			except Exception as er:
				print("GEX BOOM - ", er)
				await  intr.followup.send("Error pulling data!")
		else:
			fn = dc.drawGEXChart(ticker, count, dte, chartType=chartType)
	if fn == "error.png": await intr.followup.send("Failed to get data")
	else:
		try: await intr.followup.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await intr.followup.send("No image permissions")

@slash_command_gex.error
async def on_gex_error(intr: discord.Interaction, error: app_commands.AppCommandError):
	print( error ) #This should no longer actually be fired,  left-overs from default discord User Cooldown code
	try:
		await intr.response.send_message(f'Using /gex has a 1 minute cooldown - {int(error.retry_after)} seconds remaining', ephemeral=True)
	except: await intr.response.send_message(f'Using /gex has a 1 minute cooldown')
	
@bot.command(name="pump")
async def command_pump(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(pumps) + enc(" " + ' '.join(args) ) ) )
@bot.command(name="dump")
async def command_dump(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(dumps) + enc(" " + ' '.join(args)) ) )
@bot.command(name="tits")
async def command_tits(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(titties) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="ass")
async def command_ass(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(asses) if len( args) == 0 else enc(' '.join(args)) ) )
@bot.command(name="gm")
async def command_gm(ctx, *args): await legacySend( ctx=ctx, text= getTenorGIF( random.choice(gms) if len( args) == 0 else enc(' '.join(args)) ) )
	
@bot.tree.command(name="8ball", description="Answers your question?")
async def slash_command_8ball(intr: discord.Interaction, question: str):
	perms = await checkInteractionPermissions( intr )
	future = ['Try again later', 'No', 'Yes, absolutely', 'It is certain', 'Outlook not so good', 'You should ask Siri, that slut.', 'I rolled a dice to answer you, and it said the answer is C.', 'Follow your heart, I wouldn\'t trust your mind though.', 'I don\'t know and I don\'t care.', 'Did you ask ChatGPT?', 'Just google it.']
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

@bot.tree.command(name="news")
async def slash_command_news(intr: discord.Interaction, days: str = "TODAY"):	
	perms = await checkInteractionPermissions( intr )
	await intr.response.defer(thinking=True)

	finalMessage, nextMessage = buildNews(days)
	chnl = bot.get_channel(intr.channel.id)
	try: 
		#await intr.response.send_message( finalMessage )
		await intr.followup.send( finalMessage )
	except Exception as e: 
		try: await legacySend( channel=chnl, text=finalMessage )
		except Exception as er: print("News BOOM", er)
	if len(nextMessage) != 0:
		try: await legacySend( channel=chnl, text=nextMessage )	
		except Exception as e: print("News 2 BOOM", e)

@bot.command(name="sudo")
@commands.is_owner()
async def sudo(ctx, *args): 
	global tickers, updateRunning, auto_updater, update_timer
	user = str(ctx.author.name)
	userID = ctx.author.id
	print( user, userID )
	if 758033219177283696 != userID:
		await legacySend( ctx=ctx, text=user + " you can't kill meme!")
		return
	if len(args) != 1 : 
		await legacySend( ctx=ctx, text="No command")
		return

	if args[0] == "kill" :
		await legacySend( ctx=ctx, text=user + " triggered shutdown")
		await bot.close()
		await bot.logout()
		exit(0)
	elif args[0] == "update" :
		await legacySend( ctx=ctx, text=user + " requested code update")
		print("getting update")
		files = ['discordbot.py', 'datapuller.py', 'drawchart.py', 'signals.py']
		for fileName in files:
			print(f'Fetching {fileName}')
			r = requests.get(url=f'https://raw.githubusercontent.com/Smayxor/stock/main/{fileName}')
			
			with open(f'./{fileName}', "wb") as outfile:
				outfile.write(r.content)
				print(f'{fileName} Downloaded at {os.path.realpath(outfile.name)} - {outfile.name}' )
		print('All files updated.  Restarting service')
		exit(9)
		await bot.close()
		await bot.logout()
	print("Finished SUDO")	
	
	await legacySend( ctx=ctx, text="Command Complete")

dailyTaskTime = datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime)
async def dailyTask():
	chnl = bot.get_channel(UPDATE_CHANNEL)
	if datetime.datetime.now().weekday() > 4 : 
		await legacySend( channel=chnl, text= buildNews("WEEK")[0] )
		return
	#print("Daily Task Execution")
	await legacySend( channel=chnl, text="Fetching Morning Charts")
	await legacySend( channel=chnl, text= buildNews("TODAY")[0] )
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await chnl.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await legacySend( channel=chnl, text="No image permissions")
		
	if datetime.datetime.now().weekday() == 0 : 
		fn = dc.drawWeeklyChart()
		chnl = bot.get_channel(1221522301787570256)
		await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		chnl = bot.get_channel(1258440980529418250)  #Beating Meat Gex Channel
		await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))

dailyTaskTime2 = datetime.time(hour=13, minute=31, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime2)
async def dailyTask2():
	if datetime.datetime.now().weekday() > 4 : return
	chnl = bot.get_channel(UPDATE_CHANNEL)
	#print("Daily Task Execution 2")
	dp.findSPY2SPXRatio()
	legacySend( channel=chnl, text="Fetching Morning Charts")
	fn = dc.drawGEXChart("SPX", 40, 0)
	if fn == "error.png": await legacySend( channel=chnl, text="Failed to get data")# await chnl.send("Failed to get data")
	else:
		try: 
			chnl = bot.get_channel(UPDATE_CHANNEL)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			chnl = bot.get_channel(1156977360881586177)
			await legacySend( channel=chnl, fileName=fn)#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
		except: await legacySend( channel=chnl, text="No image permissions")#await chnl.send("No image permissions")
	#logFutureDTEs() #For Heatmap

dailyTaskTime3 = datetime.time(hour=13, minute=11, tzinfo=datetime.timezone.utc)#utc time is + 7hrs
@tasks.loop(time=dailyTaskTime3)
async def dailyTask3():
	if datetime.datetime.now().weekday() > 4 : return
	chnl = bot.get_channel(1193060258088759356)
	#print("Daily Task Execution 3")
	fn = dc.drawGEXChart("SPX", 40, 0)#, chartType=CHART_VOLUME)
	if fn == "error.png": await legacySend( channel=chnl, text="Failed to get data")

	else:
		try: 
			chnl = bot.get_channel(1193060258088759356)
			#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			await legacySend( channel=chnl, fileName=fn)
			chnl = bot.get_channel(UPDATE_CHANNEL)
			#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			await legacySend( channel=chnl, fileName=fn)
			chnl = bot.get_channel(1258440980529418250)  #Beating Meat gex channel
			#await chnl.send(file=discord.File(open('./' + fn, 'rb'), fn))
			await legacySend( channel=chnl, fileName=fn)
		except: await legacySend( channel=chnl, text="No image permissions")

blnFirstTime = True
@bot.event
async def on_ready():
	global blnFirstTime
	if blnFirstTime :
		#channelUpdate.start()
		dailyTask.start()
		dailyTask2.start()
		dailyTask3.start()
		blnFirstTime = False
	
@bot.command(name="s")
async def get_gex(ctx, *args):
	chnl = bot.get_channel(UPDATE_CHANNEL)
	await legacySend( channel=chnl, text="Testing stuff")
	#*********************************************************************************************************************

@bot.command(name="listg")
@commands.is_owner()
async def listg(ctx, *args):  #Needs customized so the arguements remove you from a server etc......meh
	user = str(ctx.author)
	if BOT_USER_FOR_KILL != user:
		await legacySend( ctx=ctx, text=user + " you can't kill meme!")
		return
		
	blnExit = args[0] == 'leave'
		
	txt = ""
	for guild in bot.guilds:
		if blnExit :
			blnFound = False
			for i in range(1, len(args) ):
				if args[i] in  guild.name : blnFound = True
			txt += '********** Staying in - ' if blnFound else 'Leaving - '
			if blnFound == False :
				await guild.leave() # Guild found
		txt += guild.name + '\r'
	await legacySend( ctx=ctx, text=f"{txt}")

"""
@commands.listener()
async def on_guild_join(guild):
	#cli = self.client
	ctx = bot.get_context
	await ctx.create_text_channel("📯announcements-and-suggestions")
	await ctx.create_text_channel("💼log")               
	general = find(lambda x: x.name == '📯announcements-and-suggestions',  guild.text_channels)
	if general and general.permissions_for(guild.me).send_messages:
		await ctx.send(f"Hello {guild.name}! I am {self.client.user.display_name}. Thank you for inviting me.\n\nTo see what commands I have available type `r?help`.\nIf you want to see my available AutoResponse Triggers type `gethelp`.")
"""
	
@bot.command(name="news")
async def news(ctx):
	#chnl = bot.get_channel(UPDATE_CHANNEL)
	#await ctx.send( buildNews("WEEK")[0] )
	await legacySend( ctx=ctx, text=buildNews("WEEK")[0] )

#    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
#    @commands.hybrid_command(name="adventure", aliases=["a"])
#    @commands.bot_has_permissions(add_reactions=True)

@bot.command(name="test")
async def test(ctx):
	if BOT_USER_FOR_KILL != str(ctx.author): return   #Honestly NEEDS to use   ctx.author.id
	channel = ctx.channel
	#channel = bot.get_channel(1259405215820550255)  #Testing channel
	permissions = channel.permissions_for(ctx.guild.me)
	textable = permissions.send_messages == True
	imageable = permissions.attach_files == True
	await legacySend( ctx, channel=channel, fileName=f'stock-chart.png')
	await legacySend( ctx, channel=channel, text=f'Text {textable} and Images {imageable}')

#ctx = 'args', 'author', 'bot', 'bot_permissions', 'channel', 'clean_prefix', 'cog', 'command', 'command_failed', 'current_argument', 'current_parameter', 'defer', 'fetch_message', 'filesize_limit', 'from_interaction', 'guild', 'history', 'interaction', 'invoke', 'invoked_parents', 'invoked_subcommand', 'invoked_with', 'kwargs', 'me', 'message', 'permissions', 'pins', 'prefix', 'reinvoke', 'reply', 'send', 'send_help', 'subcommand_passed', 'typing', 'valid', 'view', 'voice_client'
async def legacySend(ctx=None, channel=None, text=None, fileName=None):  #When not using /commands Check channel permissions before sending ALWAYS
	if channel == None : channel = ctx.channel
	#channel in DM = 'id', 'jump_url', 'me', 'permissions_for', 'pins', 'recipient', 'recipients', 'send', 'type', 'typing'
	#channel in Channel = 'archived_threads', 'category', 'category_id', 'changed_roles', 'clone', 'create_invite', 'create_thread', 'create_webhook', 'created_at', 'default_auto_archive_duration', 'default_thread_slowmode_delay', 'delete', 'delete_messages', 'edit', 'fetch_message', 'follow', 'get_partial_message', 'get_thread', 'guild', 'history', 'id', 'invites', 'is_news', 'is_nsfw', 'jump_url', 'last_message', 'last_message_id', 'members', 'mention', 'move', 'name', 'nsfw', 'overwrites', 'overwrites_for', 'permissions_for', 'permissions_synced', 'pins', 'position', 'purge', 'send', 'set_permissions', 'slowmode_delay', 'threads', 'topic', 'type', 'typing', 'webhooks'

	if "private" in channel.type :  #"text" in channel.type = in a Channel.     May also use if channel.guild is None
		permissions = ctx.permissions
	else :
		permissions = channel.permissions_for(channel.guild.me) 
	if text != None and permissions.send_messages == True : await channel.send( text )
	if fileName != None and permissions.attach_files == True :
		await channel.send(file=discord.File(open('./' + fileName, 'rb'), fileName))

@bot.command(name="list")
async def list(ctx):
	await legacySend( ctx=ctx, text=str(dp.pullLogFileList()) )

@bot.command(name="pc")
async def pc(ctx, *args):
	try:
		if 'help' in args[0] :#or len(args) < 3: 
			await ctx.send( '}pc Options Price Chart.\rSimply type =pc SPY/SPX day strikec or strikep.\r=pc SPX 11-06 4450c 4425p 4500c\rYou can also type =list to get a list of available days' )
			return
		ticker = 'SPX' #if args[0].upper() == 'SPX' else 'SPY'
		fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
		file = fileList[-1]
		
		gexData = dp.pullLogFile(file, discordBot=True)
		chart = dc.drawPriceChart( ticker, file, gexData, args )
	
		#await ctx.send( file=discord.File(open('./' + chart, 'rb'), chart) )
		await legacySend( ctx=ctx, fileName = chart )
	except:
		await legacySend( ctx=ctx, text="Error drawing price chart" )
		#await ctx.send( "Error drawing price chart" )

@bot.tree.command(name="pc")
@commands.is_owner()
async def slash_command_pc(intr: discord.Interaction, strike1: str = "all", strike2: str = "spx"):
	perms = await checkInteractionPermissions( intr )
	await intr.response.defer(thinking=True, ephemeral=perms[3]==False)
	#chnl = bot.get_channel(intr.channel.id)
	try: 
		#await intr.response.send_message( finalMessage )
		ticker = 'SPX' #if args[0].upper() == 'SPX' else 'SPY'
		fileList = [x for x in dp.pullLogFileList() if '0dte' in x]
		file = fileList[-1]
		gexData = dp.pullLogFile(file, discordBot=True)
		chart = dc.drawPriceChart( ticker, file, gexData, [strike1, strike2] )
		await intr.followup.send(file=discord.File(open('./' + chart, 'rb'), chart))
	except: await intr.followup.send("No image permissions")

@bot.command(name="heatmap")
async def heatmap(ctx, *args):
	print("Fetching % based heatmap")
	try:
		fileName = dc.drawPrecentageHeatMap('SPX', 100, 1)
		await legacySend( ctx=ctx, fileName=fileName )
	except: pass
	
@bot.command(name="ph")
async def ph(ctx, *args):  #Grabs Morning GEX Chart for Xdte 
	try:
		ticker = 'SPX'
		index = int( args[0] )
		fileList = [x for x in dp.pullLogFileList() if ((ticker=='SPX') ^ ('SPY' in x))]
		file = fileList[ index ]

		gexData = dp.pullLogFile(file)
		day = file.replace('-datalog.json', '')
		minute = next(iter(gexData))
		price = gexData[minute]['price']
		strikes = gexData[minute]['data']
		chart = dc.drawGEXChart('SPX', 40, 0, chartType = 0, strikes = strikes, expDate = day, price = price)
	
		await legacySend( ctx=ctx, fileName=chart )
	except:
		await legacySend( ctx=ctx, text="Error drawing price chart" )

def getDateOfFriday():
	today = datetime.date.today()
	return str(today + datetime.timedelta( (4-today.weekday()) % 7 ))
	
def grabFridayCombo(dte):
	exps = dp.getExpirations('SPX')
	today = str(datetime.date.today()).split(":")[0]
	#if today == exps[0] : exps.pop(0)
	fridayIndex = exps.index(getDateOfFriday())
	exps = exps[:fridayIndex + 1]
	if 0 < dte < 5 : exps = exps[:dte+1]
	
	days = []
	startDate = None
	lastDate = ""
	for day in exps:
		opts = dp.getOptionsChain("SPX", 0, date=day )
		lastDate = opts[0]
		if startDate == None : startDate = opts[0]
		days.append( dp.getGEX( opts[1] ) )
		
	combinedData = days[0]
	for d in range( 1, len(days) ):
		nd = days[d]
		for strike in nd :
			oStrike = next((x for x in combinedData if x[dp.GEX_STRIKE] == strike[dp.GEX_STRIKE]), None)
			if oStrike == None :	
				combinedData.append( strike )
				continue
			oStrike[dp.GEX_TOTAL_GEX] += strike[dp.GEX_TOTAL_GEX]
			oStrike[dp.GEX_TOTAL_OI] += strike[dp.GEX_TOTAL_OI]
			oStrike[dp.GEX_CALL_GEX] += strike[dp.GEX_CALL_GEX]
			oStrike[dp.GEX_PUT_GEX] += strike[dp.GEX_PUT_GEX]
			oStrike[dp.GEX_CALL_OI] += strike[dp.GEX_CALL_OI]
			oStrike[dp.GEX_PUT_OI] += strike[dp.GEX_PUT_OI]
			oStrike[dp.GEX_CALL_VOLUME] += strike[dp.GEX_CALL_VOLUME]
			oStrike[dp.GEX_PUT_VOLUME] += strike[dp.GEX_PUT_VOLUME]
			#oStrike[dp.GEX_] += strike[dp.GEX_]
			#oStrike[dp.GEX_] += strike[dp.GEX_]
	#drawGEXChart(ticker, count, dte, chartType = 0, strikes = None, expDate = 0, price = 0, RAM=False):
	price = dp.getPrice("SPX", combinedData )
	fn = dc.drawGEXChart("SPX", 40, 0, 5, combinedData, expDate=f'{lastDate}-C', price=price)
	return fn

def getToday():
	dateAndtime = str(datetime.datetime.now()).split(" ")
	tmp = dateAndtime[1].split(".")[0].split(":")
	minute = (float(tmp[0]) * 10000) + (float(tmp[1]) * 100) + float(tmp[2])
	return (dateAndtime[0], minute)

TodaysUsers = {}
TodaysUsers['today'] = getToday()[0]
def confirmUser(userID):
	global TodaysUsers
	tday = getToday()
	if not tday[0] in TodaysUsers['today'] : #Start a new day.   Likely Not important to do this
		#TodaysUsers = {}
		TodaysUsers['today'] = tday[0]
	if userID in TodaysUsers :
		userCooldown = tday[1]-TodaysUsers[userID]
		if userCooldown > 20 :
			TodaysUsers[userID] = tday[1]
			return 0
		else :
			return 20 - userCooldown
	else :
		TodaysUsers[userID] = tday[1]
		return 0

#@app_commands.checks.has_permissions(moderate_members=True)
async def checkInteractionPermissions(intr: discord.Interaction):
	userID = intr.user.id
	coolDown = confirmUser(f'{intr.user.global_name}-{intr.user.display_name}#{userID}')
	#intr in a Channel = 'app_permissions', 'application_id', 'channel', 'channel_id', 'client', 'command', 'command_failed', 'context', 'created_at', 'data', 'delete_original_response', 'edit_original_response', 'entitlement_sku_ids', 'entitlements', 'expires_at', 'extras', 'followup', 'guild', 'guild_id', 'guild_locale', 'id', 'is_expired', 'is_guild_integration', 'is_user_integration', 'locale', 'message', 'namespace', 'original_response', 'permissions', 'response', 'token', 'translate', 'type', 'user', 'version'
	
	if intr.guild_id is None : return (userID, coolDown, True, True)  #We are in a DM and can do anything we want
	permissions = intr.permissions
	textable = permissions.send_messages == True
	imageable = permissions.attach_files == True
	return ( userID, coolDown, textable, imageable )

@bot.command(name="listusers")
@commands.is_owner()
async def legacyListUsers(ctx, *args):
	txt = ""
	for name in TodaysUsers:
		txt += name + "\r"
	await legacySend( ctx=ctx, text=txt )
	
bot.run(BOT_TOKEN) #Last line of code, until bot is closed

#wsb - 725851172266573915
#gex - 1055967445208281288

#intr.guild = ['_PREMIUM_GUILD_LIMITS', '__annotations__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '_add_channel', '_add_member', '_add_role', '_add_thread', '_afk_channel_id', '_banner', '_channels', '_clear_threads', '_create_channel', '_create_unavailable', '_discovery_splash', '_filter_threads', '_from_data', '_icon', '_incidents_data', '_large', '_member_count', '_members', '_public_updates_channel_id', '_remove_channel', '_remove_member', '_remove_role', '_remove_thread', '_remove_threads_by_channel', '_resolve_channel', '_roles', '_rules_channel_id', '_safety_alerts_channel_id', '_scheduled_events', '_splash', '_stage_instances', '_state', '_store_thread', '_system_channel_flags', '_system_channel_id', '_threads', '_update_voice_state', '_voice_state_for', '_voice_states', '_widget_channel_id', 'active_threads', 'afk_channel', 'afk_timeout', 'approximate_member_count', 'approximate_presence_count', 'audit_logs', 'ban', 'banner', 'bans', 'bitrate_limit', 'bulk_ban', 'by_category', 'categories', 'change_voice_state', 'channels', 'chunk', 'chunked', 'create_automod_rule', 'create_category', 'create_category_channel', 'create_custom_emoji', 'create_forum', 'create_integration', 'create_role', 'create_scheduled_event', 'create_stage_channel', 'create_sticker', 'create_template', 'create_text_channel', 'create_voice_channel', 'created_at', 'default_notifications', 'default_role', 'delete', 'delete_emoji', 'delete_sticker', 'description', 'discovery_splash', 'dms_paused', 'dms_paused_until', 'edit', 'edit_role_positions', 'edit_welcome_screen', 'edit_widget', 'emoji_limit', 'emojis', 'estimate_pruned_members', 'explicit_content_filter', 'features', 'fetch_automod_rule', 'fetch_automod_rules', 'fetch_ban', 'fetch_channel', 'fetch_channels', 'fetch_emoji', 'fetch_emojis', 'fetch_member', 'fetch_members', 'fetch_roles', 'fetch_scheduled_event', 'fetch_scheduled_events', 'fetch_sticker', 'fetch_stickers', 'filesize_limit', 'forums', 'get_channel', 'get_channel_or_thread', 'get_emoji', 'get_member', 'get_member_named', 'get_role', 'get_scheduled_event', 'get_stage_instance', 'get_thread', 'icon', 'id', 'integrations', 'invites', 'invites_paused', 'invites_paused_until', 'kick', 'large', 'leave', 'max_members', 'max_presences', 'max_stage_video_users', 'max_video_channel_users', 'me', 'member_count', 'members', 'mfa_level', 'name', 'nsfw_level', 'owner', 'owner_id', 'preferred_locale', 'premium_progress_bar_enabled', 'premium_subscriber_role', 'premium_subscribers', 'premium_subscription_count', 'premium_tier', 'prune_members', 'public_updates_channel', 'query_members', 'roles', 'rules_channel', 'safety_alerts_channel', 'scheduled_events', 'self_role', 'shard_id', 'splash', 'stage_channels', 'stage_instances', 'sticker_limit', 'stickers', 'system_channel', 'system_channel_flags', 'templates', 'text_channels', 'threads', 'unavailable', 'unban', 'vanity_invite', 'vanity_url', 'vanity_url_code', 'verification_level', 'voice_channels', 'voice_client', 'webhooks', 'welcome_screen', 'widget', 'widget_channel', 'widget_enabled']

#discor.interaction intr
#['__annotations__', '__class__', '__class_getitem__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__orig_bases__', '__parameters__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '_app_permissions', '_baton', '_client', '_cs_command', '_cs_followup', '_cs_namespace', '_cs_response', '_from_data', '_integration_owners', '_original_response', '_permissions', '_session', '_state', 'app_permissions', 'application_id', 'channel', 'channel_id', 'client', 'command', 'command_failed', 'context', 'created_at', 'data', 'delete_original_response', 'edit_original_response', 'entitlement_sku_ids', 'entitlements', 'expires_at', 'extras', 'followup', 'guild', 'guild_id', 'guild_locale', 'id', 'is_expired', 'is_guild_integration', 'is_user_integration', 'locale', 'message', 'namespace', 'original_response', 'permissions', 'response', 'token', 'translate', 'type', 'user', 'version']

# bot
#['_BotBase__cogs', '_BotBase__extensions', '_BotBase__tree', '__aenter__', '__aexit__', '__class__', '__class_getitem__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__orig_bases__', '__parameters__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_after_invoke', '_application', '_async_setup_hook', '_before_invoke', '_call_before_identify_hook', '_call_module_finalizers', '_check_once', '_checks', '_closed', '_connection', '_enable_debug_events', '_get_state', '_get_websocket', '_handle_ready', '_handlers', '_help_command', '_hooks', '_listeners', '_load_from_module_spec', '_ready', '_remove_module_references', '_resolve_name', '_run_event', '_schedule_event', 'activity', 'add_check', 'add_cog', 'add_command', 'add_listener', 'add_view', 'after_invoke', 'all_commands', 'allowed_mentions', 'application', 'application_flags', 'application_id', 'application_info', 'before_identify_hook', 'before_invoke', 'cached_messages', 'can_run', 'case_insensitive', 'change_presence', 'check', 'check_once', 'clear', 'close', 'cogs', 'command', 'command_prefix', 'commands', 'connect', 'create_dm', 'create_guild', 'delete_invite', 'description', 'dispatch', 'emojis', 'event', 'extensions', 'extra_events', 'fetch_channel', 'fetch_guild', 'fetch_guilds', 'fetch_invite', 'fetch_premium_sticker_packs', 'fetch_stage_instance', 'fetch_sticker', 'fetch_template', 'fetch_user', 'fetch_webhook', 'fetch_widget', 'get_all_channels', 'get_all_members', 'get_channel', 'get_cog', 'get_command', 'get_context', 'get_emoji', 'get_guild', 'get_partial_messageable', 'get_prefix', 'get_stage_instance', 'get_sticker', 'get_user', 'group', 'guilds', 'help_command', 'http', 'hybrid_command', 'hybrid_group', 'intents', 'invoke', 'is_closed', 'is_owner', 'is_ready', 'is_ws_ratelimited', 'latency', 'listen', 'load_extension', 'login', 'loop', 'on_command_error', 'on_error', 'on_message', 'on_ready', 'owner_id', 'owner_ids', 'persistent_views', 'private_channels', 'process_commands', 'recursively_remove_all_commands', 'reload_extension', 'remove_check', 'remove_cog', 'remove_command', 'remove_listener', 'run', 'setup_hook', 'shard_count', 'shard_id', 'start', 'status', 'stickers', 'strip_after_prefix', 'tree', 'unload_extension', 'user', 'users', 'voice_clients', 'wait_for', 'wait_until_ready', 'walk_commands', 'ws']

#bot.user
['__annotations__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_accent_colour', '_avatar', '_banner', '_copy', '_flags', '_public_flags', '_state', '_to_minimal_user_json', '_update', 'accent_color', 'accent_colour', 'avatar', 'banner', 'bot', 'color', 'colour', 'created_at', 'default_avatar', 'discriminator', 'display_avatar', 'display_name', 'edit', 'global_name', 'id', 'locale', 'mention', 'mentioned_in', 'mfa_enabled', 'mutual_guilds', 'name', 'public_flags', 'system', 'verified']

#channel
#['__annotations__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '_apply_implicit_permissions', '_clone_impl', '_edit', '_fill_overwrites', '_get_channel', '_move', '_overwrites', '_scheduled_event_entity_type', '_sorting_bucket', '_state', '_type', '_update', 'archived_threads', 'category', 'category_id', 'changed_roles', 'clone', 'create_invite', 'create_thread', 'create_webhook', 'created_at', 'default_auto_archive_duration', 'default_thread_slowmode_delay', 'delete', 'delete_messages', 'edit', 'fetch_message', 'follow', 'get_partial_message', 'get_thread', 'guild', 'history', 'id', 'invites', 'is_news', 'is_nsfw', 'jump_url', 'last_message', 'last_message_id', 'members', 'mention', 'move', 'name', 'nsfw', 'overwrites', 'overwrites_for', 'permissions_for', 'permissions_synced', 'pins', 'position', 'purge', 'send', 'set_permissions', 'slowmode_delay', 'threads', 'topic', 'type', 'typing', 'webhooks']
