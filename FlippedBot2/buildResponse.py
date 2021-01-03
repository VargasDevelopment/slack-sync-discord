class ResponseBuilder:
    
    def __init__(self, channel, message_resp, user = "FlippedBot", avatar = ":robot_face:"):
        self.message_txt = message_resp
        self.message_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                self.message_txt
                ),
            },
        }
        self.channel = channel
        self.username = user
        self.avatar = avatar
        self.timestamp = ""
            
    def getMessagePayload(self):
        if self.avatar == ":robot_face:":
            return {
                "ts": self.timestamp,
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": self.avatar,
                "blocks": [
                    self.message_block,
                ],
            }
        else:
            return {
                "ts": self.timestamp,
                "channel": self.channel,
                "username": self.username,
                "icon_url": self.avatar,
                "blocks": [
                    self.message_block,
                ],
            }
