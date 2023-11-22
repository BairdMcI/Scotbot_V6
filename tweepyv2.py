import tweepy
import discord
from requests.exceptions import Timeout, ConnectionError
from requests.packages.urllib3.exceptions import ReadTimeoutError
import ssl
from auth import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

userList = ["quill18", "aKiss4Luck"]

webhookMessageDict = {"quill18": 635437418278944769,
                      "aKiss4Luck": 642049174438674498}

webhookIdDict = {"quill18": "PbxdE7BuDzuwiBIhhMeJGNLkaWi3Tj5SpmcvHsC5edLsBUGoDVDzIj2ogwcrE5Pn9659",
                 "aKiss4Luck": "SFkf4jTcYFS7rioKvH6t__nTpr0YAGBNPAK7ThBTgEwBLkgL9RVGZ24XAgnUq-ffNdY_"}

auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)


class StreamListener(tweepy.Stream):
    @staticmethod
    def on_status(status):
        if status.user.screen_name in userList:
            if status.in_reply_to_screen_name != status.user.screen_name and status.in_reply_to_screen_name is not None:
                return
            else:
                webhook = discord.Webhook.partial(webhookMessageDict[status.user.screen_name], webhookIdDict[status.user.screen_name], adapter=discord.RequestsWebhookAdapter())
                tweetURL = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
                webhook.send(status.user.screen_name + " has just tweeted! " + tweetURL)
                print(str(status.created_at) + " | " + status.user.screen_name + " tweeted\n")

    @staticmethod
    def on_error(statusCode):
        if statusCode == 420:
            return False


stream = StreamListener(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

print("Starting Tweepy...")
while not stream.running:
    try:
        print("Started following channels...")
        stream.filter(follow=["47691900", "30724014", "1089731137"])
    except (Timeout, ssl.SSLError, ReadTimeoutError, ConnectionError) as e:
        print(e)
    except Exception as e:
        print(e)
    

