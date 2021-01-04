import os
from dotenv import load_dotenv
import logging
from flask import Flask
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
from buildResponse import ResponseBuilder
from kafka import KafkaProducer, KafkaConsumer
from json import loads, dumps
from jsonschema import validate, ValidationError
import threading

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
SECRET = os.getenv("SIGNING_SECRET")
CHANNEL = os.getenv("CHANNEL")
app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(SECRET, "/slack/events", app)

slack_web_client = WebClient(token=TOKEN)

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

translationDict = {
    "Slack Username" : "Discord_Username"
}


producer = KafkaProducer(bootstrap_servers=["localhost:9092"], value_serializer=lambda x: dumps(x).encode("utf-8"))

def consume_d2s(sc, channel):
    consumer = KafkaConsumer("d2s", bootstrap_servers=["localhost:9092"], auto_offset_reset="earliest", enable_auto_commit=True, group_id="messages", value_deserializer=lambda x: loads(x.decode("utf-8")))
    for message in consumer:
        data = message.value
        user = data["user"]
        message = data["message"]
        avatar = data["avatar"]
        sendResponse(sc, CHANNEL, message, user, avatar)    
    
def getRealName(sc, userId):
    try:
        result = sc.users_info(user=userId)
        result = result.get("user", {})
        return result["profile"]["real_name"]
    except SlackApiError as e:
        logger.error("Couldn't get that user's info: {}".format(e))

def getAvatar(sc, userId):
    try:
        result = sc.users_info(user=userId)
        result = result.get("user", {})
        return result["profile"]["image_original"]
    except SlackApiError as e:
        logger.error("couldn't get that user's avatar: {}".format(e))

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

def send_s2d(data):
    if messageIsValid(data):
        producer.send("s2d", value=data)
        print("----------------SENT TO S2D--------------------")

def handleCommand(sc, channel, msg, user, avatar):
    splitMsg = msg.lower().split()
    if splitMsg[0] == "!f":
        sendResponse(sc, channel, "FUCK!!")
    elif splitMsg[0] == "!help":
        helpMsg ="Hi! :wave: I'm FlippedBot. Eventually I'll sync messages from here and Discord, but in the meantime here are some fun commands I know:\n!f - _bot says obsenity_\n!copy - _bot impersonates you and echoes what you said_\n!help - _displays this help message_"
        sendResponse(sc, channel, helpMsg)
    elif splitMsg[0] == "!copy":
        if len(splitMsg) > 1:
            copyMsg = " ".join(splitMsg[1:])
            sendResponse(sc, channel, copyMsg, user, avatar)
        else:
            copyMsg = "You didn't send anything to copy..."
            sendResponse(sc, channel, copyMsg)
            
def sendResponse(sc, channel, msg, user="FlippedBot", avatar=":robot_face:"):
    response = ResponseBuilder(channel, msg, user=user, avatar=avatar)
    finalMsg = response.getMessagePayload()
    sc.chat_postMessage(**finalMsg)


# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'`.
# Here we'll link the message callback to the 'message' event.
@slack_events_adapter.on("message")
def message(payload):
    # Listen for messages that aren't from bots. 
    # If they seem to be commmands, send them to handleCommand()

    event = payload.get("event", {})

    if event.get("subtype") == "bot_message":
        return
    else:
        channel_id = event.get("channel")
        print(str(channel_id))
        user_id = event.get("user")
        realName = getRealName(slack_web_client, user_id)
        avatarURL = getAvatar(slack_web_client, user_id)
        text = event.get("text")
        data = jsonFactory(realName, text, avatarURL)
        if text[0] != "!":
            print("----------------SENDING TO S2D--------------------")
            send_s2d(data)
            return
        else:
            handleCommand(slack_web_client, channel_id, text, realName, avatarURL )

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    t = threading.Thread(target=consume_d2s, args=[slack_web_client, CHANNEL])
    t.start()
    app.run(port=3000)
