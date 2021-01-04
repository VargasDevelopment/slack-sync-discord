# slack-sync-discord
Bi-Directional synchronization of Slack and Discord

# Setup

## Clone the project
Use Git to clone the project to your machine

## Slack Bot
1. Using the Slack API, [create a Slack App](https://api.slack.com/apps)
2. Keep track of your Bot Token and your Signing Secret. You'll add these to a ".env" file in the future
3. Go to OAuth & Permissions, and add:
	- 'chat:write', 'chat:write.customize' and 'users:read' for Bot Token Scoptes
	- 'channels:history' for User Token Scopes
4. At the top of the OAuth & Permissions page, click "Install App to Workspace"
5. Click on "Events Subscriptions"
	- 'Turn On' Enable Events
	- Click 'Subscribe to events on behalf of users'
		- Add 'message.channels' to the permission scope.
6. Using te [Slack API Tester](https://api.slack.com/methods/conversations.list/test) and your Bot Token, get the ID of the General Channel in your Slack Server

## Discord Bot
1. Using the Discord API, [create a new discord application](https://discord.com/developers/applications)
2. Click 'New Application', and make a new Bot
3. Keep track of your Discord Token. You'll add this to a separate ".env" file in the future
4. To invite your bot to your server, click OAuth2
	- Tick the 'bot' checkbox under scopes.
	- Tick the 'Read Message History' permisson.
	- Copy the URL and paste it into your browser to add the bot to your server
4. In your Discord server, turn on developer settings.
	- Save the General channel's channel ID for the ".env" file
	- Create a webhook for the General Channel
	- Save the webhook's URL for the ".env" file

## Set up Kafka
1. Insall and set up Kafka
	- I mostly followed [this tutorial](https://hevodata.com/blog/how-to-install-kafka-on-ubuntu/)
	- Make sure you download the latest Kafka version available
2. Set up 2 Kafka topics:
	- "s2d" for messages sent from Slack to Discord
	- "d2s" for messages sent from Discord to Slack

## Set up Ngrok
1. install ngrok
2. Run 'ngrok http 3000', copy the https URL
3. In a notepad, paste, then append 'slack/events' to the end of the URL and copy it again

# Run it

## Run the Slack Bot
1. Under 'Flippedbot2', create a '.env' file and fill in the appropriate values for:
	- 'SIGNING_SECRET='
	- 'BOT_TOKEN='
	- 'CHANNEL=' 
2. Back under your Slack App's settings, click back on "Event Subscriptions"
3. Run flippedbot2.py: 'python3 flippedbot2.py'
4. Paste the URL you saved while setting up ngrok under "Request URL". It should say "Verified"

## Run Discord Bot
1. Under "DiscordBot", create a '.env' file and fill in the appropriate values for:
	- 'DISCORD_TOKEN='
	- 'DISCORD_GUILD='
	- 'DISCORD_CHANNEL='
	- 'WEBHOOK_URL='
2. Run flippedBot_D.py: 'python3 flippedBot_D.py'

# How it works
Both bots have one Kafka Consumer and one Kafka Producer. When a message is received on either end, the bot transforms a message according to a JSON schema and posts it to the corresponding Kafka topic using the Kafka Producer. The other bot consues that message using the Kafka Consumer and posts it to the chat.
