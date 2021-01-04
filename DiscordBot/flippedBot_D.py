import os
import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from dotenv import load_dotenv
from kafka import KafkaProducer, KafkaConsumer
from jsonschema import validate, ValidationError
from json import loads, dumps
from concurrent.futures.thread import ThreadPoolExecutor
import threading
import asyncio
from time import sleep
import aiohttp

translationDict = {
    "Discord_Username" : "Slack Username"
    }

schema = {
    "type" : "object",
    "properties" : {
        "user" : {"type" : "string"},
        "message" : {"type" : "string"},
        "avatar" : {"$ref": "#/definitions/Url"}
    },
    "required" : ["user", "message", "avatar"],
    "definitions" : {
        "Url" : { "format" : "uri", "pattern" : "^https?://"}
    }
}

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
CHANNEL = os.getenv("DISCORD_CHANNEL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MESSAGE = ""
USER = ""
AVATAR = ""

help_txt = "Hi! :wave: I'm FlippedBot - Discord style!\nI ferry messages from Here to slack and vice versa.\nHere is a command I know:\n!f - I yell an obsenity"

producer = KafkaProducer(bootstrap_servers=["localhost:9092"], value_serializer=lambda x: dumps(x).encode("utf-8"))

dcBot = discord.Client()

async def start_loop():
    while True:
        message = await main_loop.run_in_executor(executor, consume_s2d)

def consume_s2d():
    consumer = KafkaConsumer("s2d", bootstrap_servers=["localhost:9092"], auto_offset_reset="earliest", enable_auto_commit=True, group_id="messages", value_deserializer=lambda x: loads(x.decode("utf-8")))
    print("Kafka consuming s2d")
    tLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(tLoop)
    for message in consumer:
        print("Received message")
        data = message.value
        user = data["user"]
        message = data["message"]
        avatar = data["avatar"]
        print(data)
        task = tLoop.create_task(sendSlackMessage(user, message, avatar))
        tLoop.run_until_complete(task)
        asyncio.sleep(0.5)
        
async def sendSlackMessage(user, msg, avatar):
    print("Forwarding message..")
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(WEBHOOK_URL, adapter=AsyncWebhookAdapter(session))
        await webhook.send(msg, username=user, avatar_url=avatar)
    
    print("sent message")
    return


def messageIsValid(data):
    try:    
        validate(data,schema=schema)
        return True
    except ValidationError as e:
        print("Data failed schema validation: " + str(e))
        return False
    
def jsonFactory(name, msg, avatar):
    return {
        "user" : translationDict[name],
        "message" : msg,
        "avatar" : avatar
    }

def send_d2s(data):
    if messageIsValid(data):
        producer.send("d2s", value=data)

@dcBot.event
async def on_ready():
    print("CONNECTED TO: "+str(GUILD))
    await main_loop.run_in_executor(executor, consume_s2d)
    
@dcBot.event
async def on_message(message):
    if message.author == dcBot.user:
        return
    elif hasattr(message, "webhook_id"):
        if message.webhook_id is not None:
            return
    messageTxt = message.content
    authorName = message.author.name
    authorAvatar = str(message.author.avatar_url)
    authorAvatar = authorAvatar.split(".")
    authorAvatar = ".".join(authorAvatar[:len(authorAvatar)-1])
    authorAvatar = authorAvatar + ".png"
    
    data = jsonFactory(authorName, messageTxt, authorAvatar)
    send_d2s(data)

main_loop = asyncio.get_event_loop()
executor = ThreadPoolExecutor(max_workers=1)

main_loop.run_until_complete(dcBot.run(TOKEN))
