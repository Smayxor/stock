from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands
import tkinter as tk
from PIL import Image,ImageTk
import datapuller as dp
import drawchart as dc
import threading
import time
import math
import requests
import ujson as json
import asyncio
import websockets

init = json.load(open('apikey.json'))
BOT_TOKEN = init.get('NO_DISCORD_BOT_2', None)
del init

#import "C:\Users\hmset\Desktop\tradier\gobcog-master\adventure.py" as Adventure
#sys.path.insert(0, 'C:\Users\hmset\Desktop\tradier\gobcog-master\adventure.py')

#import sys
#sys.path.insert(0, './gobcog-master/adventure')
#import adventure

class MyBotHelp(commands.MinimalHelpCommand):
	async def send_pages(self):
		strHelp = """No Help"""
		destination = self.get_destination()
		for page in self.paginator.pages:
			await destination.send(strHelp)
bot = commands.Bot(command_prefix='}', intents=discord.Intents.all(), help_command=MyBotHelp(), sync_commands=True)

@bot.command(name="bot")
async def command_bot(ctx, *args): 
	arg = args[0]	
	if 'all' in arg : 
		e3Text.set('all')
		return
	if len(args) != 1 : await ctx.send( f'One command at a time' )
	if len(arg) != 5 : await ctx.send( f'Strike + c or p example 5425c - {len(arg)}' )
	isCall = 'c' in arg
	isPut = 'p' in arg
	if isCall == False and isPut == False : 
		await ctx.send( f'Call {isCall} - Put {isPut}' )
		return
	try :
		strike = int( arg[:4] )
	except:
		await ctx.send( f'Couldn\'t decode strike {arg[:4]}' )
		return

	if isCall :
		e3Text.set( str(strike) + 'c' )
		checkCall.set(1)
	if isPut :
		e4Text.set( str(strike) + 'p' )
		checkCall.set(0)
		
@bot.command(name="clone")
async def command_clone(ctx, *args): 	
	# ECONONMY = 804191163610824735
	# Adeventure = 1064534371144572928
	
	guild = ctx.message.guild
	await ctx.send( f'<div id="message-content-964633800422342727" class="markup_f8f345 messageContent_f9f2ca"><span>gn frens</span></div>' )

#@tasks.loop(time=dailyTaskTime)
#async def dailyTask():
#	chnl = bot.get_channel(1257557696006066346)

@bot.event
async def on_message(msg):
	print( msg )
	if msg.content is not None:
		print(msg.content)
		print(msg.reactions)
		#await msg.add_reaction("Fight")  :dagger:
	await bot.process_commands(msg)

@commands.command()
async def reaction(ctx, msg: discord.Message):
#	await msg.add_reaction(u"\U0001F3AB")
	await msg.add_reaction("Fight")
	
@bot.command(name="stop")
async def command_stop(ctx, *args): 
	await bot.close()
	await bot.logout()
	exit(0)

bot.run(BOT_TOKEN)

#<div id="message-content-964633800422342727" class="markup_f8f345 messageContent_f9f2ca"><span>gn frens</span></div>


#React with: **Fight** - **Spell** - **Talk** - **Pray** - **Run**
#<Message id=1258703213226627102 channel=<TextChannel id=1257557696006066346 name='adventure' position=7 nsfw=False news=False category_id=1257557668927639644> type=<MessageType.default: 0> author=<Member id=1057095478120034385 name='wsbx' global_name=None bot=True nick=None guild=<Guild id=725382837292892251 name='Commands' shard_id=0 chunked=True member_count=10>> flags=<MessageFlags value=0>>
#⏳ [Time remaining] <t:1720169456:R>




"""
import discord
import websockets
import asyncio

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot1 ist eingeloggt als {client.user}')

@client.event
async def on_message(message):
    if message.content == '!test':
        async with websockets.connect('ws://localhost:8765') as websocket:
            await websocket.send('Test command received')

client.run('TOKEN_BOT1')

import discord
import websockets
import asyncio

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot2 ist eingeloggt als {client.user}')

async def listen_for_commands():
    async with websockets.serve(handler, 'localhost', 8765):
        await asyncio.Future()  # Run forever

async def handler(websocket, path):
    async for message in websocket:
        channel = client.get_channel(YOUR_CHANNEL_ID)
        await channel.send('Test command received on Bot1')

client.loop.create_task(listen_for_commands())
client.run('TOKEN_BOT2')
"""