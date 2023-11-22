import asyncio

import twitchio
from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel


class SubscriptionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    def rawUsernoticeCheck(self, channelObj: twitchio.Channel, tags: dict) -> bool:
        if tags["msg-id"] in ["subgift","anonsubgift"]:
            channel: Channel = self.bot.channels[channelObj.name]
            subGiver = "Anonymous" if tags["display-name"] == channel.name else tags["display-name"]
            subReceiver = tags["msg-param-recipient-display-name"]
            if subGiver not in channel.giftsubs:
                channel.giftsubs[subGiver] = []
            if subReceiver not in channel.giftsubs[subGiver]:
                channel.giftsubs[subGiver].append(subReceiver)
                return True
        return False

    @commands.Cog.event()
    async def event_raw_usernotice(self, channelObj: twitchio.Channel, tags: dict):
        msgID = tags["msg-id"]
        if msgID == "raid":
            raiderChannel = tags["display-name"]
            raiderCount = tags["msg-param-viewerCount"]
            self.bot.logger.info(f"{raiderChannel} raided {channelObj.name} with {raiderCount} viewers")
            await channelObj.send(f"Please welcome the {raiderCount} raiders from {raiderChannel}!")

        elif tags["msg-id"] in ["subgift", "anonsubgift"]:
            while True:
                try:
                    await self.bot.wait_for(event="raw_usernotice", predicate=self.rawUsernoticeCheck, timeout=1)
                except asyncio.TimeoutError:
                    break
            channel: Channel = self.bot.channels[channelObj.name]
            for gifter, receivers in channel.giftsubs.items():
                self.bot.logger.info(f"Sub gift from {gifter} to {'; '.join(receivers)} in '{channelObj.name}'")
                await channelObj.send(f"Thank you to {gifter} for gifting a sub to {'; '.join(receivers)}! <3")
            channel.giftsubs = {}

        elif tags["msg-id"] == "ritual":
            newChatter = tags["display-name"]
            self.bot.logger.info(f"{newChatter} is new to '{channelObj.name}'")
            await channelObj.send(f"Please welcome @{newChatter} to the channel!")

        elif tags["msg-id"] == "sub":
            user = tags["display-name"]
            self.bot.logger.info(f"{user} subscribed to '{channelObj.name}'")
            await channelObj.send(f"Thanks for the sub @{user}, and welcome tae aw the fun! <3")

        elif tags["msg-id"] == "resub":
            user = tags["display-name"]
            self.bot.logger.info(f"{user} resubscribed to '{channelObj.name}'")
            await channelObj.send(f"Thanks for the {tags['msg-param-cumulative-months']}-month resub, @{user} - Welcome back! <3")


def prepare(bot):
    bot.add_cog(SubscriptionsCog(bot))
