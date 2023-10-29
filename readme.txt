****  Rebuilding everything to use Tradier API.   ****

For basic usage with only a TDA Developer account run stock.py    it has optional gui and server arguements
The server is for discord bot, which requires you to make a discord developer account and create an app.
To run without discord bot
python3 stock.py gui
To run with discord bot
python3 stock.py server
Leaving out the arguement should run as both.

If you have a TDA account you can sign up for OPRA and get Live Data instead of Delayed Data.  This will require you to run oath.py
python3 oath.py gui         or      python3 oath.py server
You will first have to uncomment the HTTPServer section.  Then run this link in a web browser

https://auth.tdameritrade.com/oauth?client_id=(YOUR_API_KEY_HERE)%40AMER.OAUTHAP&response_type=code&redirect_uri=https%3A%2F%2Flocalhost%3A8080%2F

I hope to add a login bot in the future.  The HTTPServer is commented out as it is only needed every 90 days when Refresh Token expires

You will need to create an apikey.json file and fill it with your values.  Its contents should be

{"API_KEY": "YourTDADeveloperAPIKey", "BOT_TOKEN": "TokenFromYourDiscordBotApp", "BOT_KILL_USER": "YourDiscordUserName"}

You can also leave HTTPServer commented, and just fetch the tokens from TDA Developer website by following Simple Auth for Local Apps Guide, and save contents in access-token.json
