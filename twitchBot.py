import asyncio
import logging
import os
import pathlib
import re
import sqlite3
import sys
import traceback
import webbrowser
from abc import ABC
from datetime import datetime
from time import strftime

import requests
from requests_oauthlib import OAuth2Session

import twitchio
import json

from twitchio import models
from twitchio.ext.routines import routine

import logger as _logger
from twitchClasses import Channel, Giveaway, SongRequest
from auth import twitchToken, twitchClientID, twitchClientSecret

from twitchio.ext import commands, pubsub

from databaseFunctions import getAllChannelInfo

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
_logger.setupLogger(LOGGER)
LOGGER.propagate = False

scope = ["channel:read:redemptions", "chat:read"]


def token_saver(token):
    with open("data/twitch_token.json", "w") as f:
        json.dump(token, f)


def get_token(client_id, client_secret, redirect_uri, channelName):
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = oauth.authorization_url("https://id.twitch.tv/oauth2/authorize")
    webbrowser.open_new(authorization_url)

    authorization_response = input('Enter the full callback URL: ').strip()
    token = oauth.fetch_token("https://id.twitch.tv/oauth2/token", include_client_id=True, client_secret=client_secret,
                              authorization_response=authorization_response, force_querystring=True)
    token["channel"] = channelName
    token_saver(token)
    return token


def validate(oauth: OAuth2Session, channelName, can_refresh=True):
    try:
        r = requests.get('https://id.twitch.tv/oauth2/validate',
                         headers={'Authorization': f'OAuth {oauth.token["access_token"]}'})
        # print(r.text)
        r.raise_for_status()
    except requests.HTTPError as e:
        if can_refresh:
            token = oauth.refresh_token(oauth.auto_refresh_url)
            token_saver(token)
            oauth_ = get_session(twitchClientID, twitchClientSecret, 'https://localhost', channelName=channelName)
            validate(oauth_, False)
        else:
            logging.fatal("Validation failed: " + str(e))
            raise RuntimeError("Validation failed")


def get_session(client_id, client_secret, redirect_uri, channelName):
    try:
        with open("data/twitch_token.json", 'r') as f:
            token = json.load(f)
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        print("Failed to load token!")
        token = get_token(client_id, client_secret, redirect_uri, channelName)

    oauth = OAuth2Session(client_id, token=token, auto_refresh_url="https://id.twitch.tv/oauth2/token",
                          auto_refresh_kwargs={'client_id': client_id, 'client_secret': client_secret},
                          redirect_uri=redirect_uri, scope=scope, token_updater=token_saver)

    validate(oauth, channelName)
    return oauth


class Scotbot(commands.Bot, ABC):
    def __init__(self):
        con = sqlite3.connect("data/generalTwitchInfo.db")
        self.channels: dict[str: Channel] = {channel.name: channel for channel in getAllChannelInfo(con)}
        super().__init__(prefix="!",
                         token=twitchToken,
                         client_id=twitchClientID,
                         client_secret=twitchClientSecret,
                         nick="ScotBotM8",
                         initial_channels=[*self.channels],
                         case_insensitive=True)
        self.pubsub_client = None
        self.logger = LOGGER
        cogs = [f"{p.parent}.{p.stem}" for p in pathlib.Path("twitch_cogs").glob("*.py")]
        for cog in cogs:
            self.load_module(cog)
        LOGGER.info(f"Loaded cogs: {'; '.join([cog.split('twitch_cogs.')[1] for cog in cogs])}")

    async def event_ready(self):
        LOGGER.info(f"Scotbot joined Twitch Channels: {'; '.join([*self.channels])}")
        for channel in self.channels.values():
            if len(channel.giveaways) > 0:
                LOGGER.info(f"{channel.name} has open giveaway(s): {'; '.join([*channel.giveaways])}")
                for giveaway in channel.giveaways.values():
                    self.loop.create_task(giveaway.saveEntrantsLoop())

            if channel.poll is not None:
                LOGGER.info(f"{channel.name} has an open poll")
                self.loop.create_task(channel.poll.updateLoop())

            if len(channel.songs) > 0:
                LOGGER.info(f"{channel.name} has songs in the request queue: {'; '.join([song.song for song in channel.songs])}")
            self.loop.create_task(channel.saveChatLogsLoop())
            channel.channelObj = self.get_channel(channel.name)

        pubsub_sess = get_session(twitchClientID, twitchClientSecret, "https://localhost", "deadm8")
        self.pubsub_client = twitchio.Client(token=pubsub_sess.token['access_token'], initial_channels=['deadm8'], client_secret=twitchClientSecret)
        self.pubsub_client.pubsub = pubsub.PubSubPool(self.pubsub_client)
        self.loop.create_task(self.runPubsub())

        # self.cogs.get("GamesCog").updateGamesListRoutine.start()
        # await self.pubsub_client.pubsub.subscribe_topics([pubsub.channel_points(self.pubsub_client._http.token)[56403701]])
        # await self.pubsub_client.connect()

        # client.pubsub = pubsub.PubSubPool(client)
        # self.pubsub_nonce = client
        # await self.pubsub_nonce.pubsub.subscribe_topics([pubsub.channel_points(sess.token["access_token"])[56403701]])
        # await self.pubsub_nonce.connect()

    async def runPubsub(self):
        topics = [pubsub.channel_points(self.pubsub_client._http.token)[56403701]]
        await self.pubsub_client.pubsub.subscribe_topics(topics)

    async def event_pubsub_channel_points(self, event: pubsub.PubSubChannelPointsMessage):
        print(event)

    #
    # async def runPubsubs(self):
    #     await client.pubsub.subscribe_topics([pubsub.channel_points(self._http.token)[self.channels["deadm8"].id]])
    #     await client.start()

    async def event_message(self, message: twitchio.Message):
        if message.echo and message.channel.name != "jtv":
            LOGGER.log(7, f"{message.channel.name} | {message.content}")
            return

        if message.channel is None and not message.echo:
            LOGGER.log(5, f"WHISPER[{message.author.name}] | {message.content}")
            return

        if message.channel.name == "jtv":
            user = message.content.split("/w ")[1].split(" ")[0]
            logLevel = 7 if message.echo else 5
            messageContent = message.content.split(f"/w {user} ")[1]
            LOGGER.log(logLevel, f"WHISPER[{user}] | {messageContent}")
            return

        LOGGER.log(5, f"{message.channel.name} | {message.author.name}: {message.content}")
        channelInfo: Channel = self.channels[message.channel.name]
        channelInfo.chatLogs.append((strftime('%d/%m/%Y %H:%M:%S'), message.author.name, message.content))

        if len(channelInfo.giveaways) > 0:
            for keyword, giveaway in channelInfo.giveaways.items():
                if message.content.lower().startswith(keyword):
                    if message.author.name not in giveaway.entrants and message.author.name not in giveaway.winners:
                        giveaway.entrants.append(message.author.name)
                        await message.author.send(f"You have successfully entered the giveaway '{keyword}'!")

        if message.tags.get("first-msg") == "1":
            await message.channel.send(f"Please welcome @{message.author.display_name} to the channel!")

        await self.handle_commands(message)

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            pass
        else:
            LOGGER.error(f"[{ctx.channel.name}] {error}")
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_raw_usernotice(self, channel, tags: dict):
        msgID = tags["msg-id"]
        if msgID == "raid":
            raiderChannel = tags["display-name"]
            raiderCount = tags["msg-param-viewerCount"]
            LOGGER.info(f"{raiderChannel} raided {channel} with {raiderCount} viewers")
            await channel.send(f"Please welcome the {raiderCount} raiders from {raiderChannel}!")

        elif tags["msg-id"] == "subgift":
            subGiver = tags["display-name"]
            subReceiver = tags["msg-param-recipient-display-name"]
            LOGGER.info(f"Sub gift from {subGiver} to {subReceiver} in '{channel.name}'")
            await channel.send(f"Thank you to {subGiver} for gifting a sub to {subReceiver}! <3")

        elif tags["msg-id"] == "anonsubgift":
            subGiver = "Anonymous"
            subReceiver = tags["msg-param-recipient-display-name"]
            LOGGER.info(f"Anonymous sub gift to {subReceiver} in '{channel.name}'")
            await channel.send(f"Thank you to {subGiver} for gifting a sub to {subReceiver}! <3")

        elif tags["msg-id"] == "ritual":
            newChatter = tags["display-name"]
            LOGGER.info(f"{newChatter} is new to '{channel.name}'")
            await channel.send(f"Please welcome @{newChatter} to the channel!")

        elif tags["msg-id"] == "sub":
            user = tags["display-name"]
            LOGGER.info(f"{user} subscribed to '{channel.name}'")
            await channel.send(f"Thanks for the sub @{user}, and welcome tae aw the fun! <3")

        elif tags["msg-id"] == "resub":
            user = tags["display-name"]
            LOGGER.info(f"{user} resubscribed to '{channel.name}'")
            await channel.send(f"Thanks for the {tags['msg-param-cumulative-months']}-month resub, @{user} - Welcome back! <3")


if __name__ == "__main__":
    # pubsub_sess = get_session(twitchClientID, twitchClientSecret, "https://localhost", "deadm8")
    # client = twitchio.Client(token=pubsub_sess.token['access_token'], initial_channels=['deadm8'], client_secret=twitchClientSecret)
    #
    # client.pubsub = pubsub.PubSubPool(client)
    #
    #
    # @client.event()
    # async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    #     print("xYZ")
    #     await bot.event_pubsub_channel_points(event)
    #

    bot = Scotbot()
    # bot.pubsub_client = client
    bot.run()
