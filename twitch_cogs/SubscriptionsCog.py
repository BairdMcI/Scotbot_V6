from twitchio.ext import commands

from twitchBot import Scotbot


class SubscriptionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot
    
    @commands.Cog.event()
    async def event_raw_usernotice(self, channel, tags: dict):
        msgID = tags["msg-id"]
        if msgID == "raid":
            raiderChannel = tags["display-name"]
            raiderCount = tags["msg-param-viewerCount"]
            self.bot.logger.info(f"{raiderChannel} raided {channel} with {raiderCount} viewers")
            await channel.send(f"Please welcome the {raiderCount} raiders from {raiderChannel}!")

        elif tags["msg-id"] == "subgift":
            subGiver = tags["display-name"]
            subReceiver = tags["msg-param-recipient-display-name"]
            self.bot.logger.info(f"Sub gift from {subGiver} to {subReceiver} in '{channel.name}'")
            await channel.send(f"Thank you to {subGiver} for gifting a sub to {subReceiver}! <3")

        elif tags["msg-id"] == "anonsubgift":
            subGiver = "Anonymous"
            subReceiver = tags["msg-param-recipient-display-name"]
            self.bot.logger.info(f"Anonymous sub gift to {subReceiver} in '{channel.name}'")
            await channel.send(f"Thank you to {subGiver} for gifting a sub to {subReceiver}! <3")

        elif tags["msg-id"] == "ritual":
            newChatter = tags["display-name"]
            self.bot.logger.info(f"{newChatter} is new to '{channel.name}'")
            await channel.send(f"Please welcome @{newChatter} to the channel!")

        elif tags["msg-id"] == "sub":
            user = tags["display-name"]
            self.bot.logger.info(f"{user} subscribed to '{channel.name}'")
            await channel.send(f"Thanks for the sub @{user}, and welcome tae aw the fun! <3")

        elif tags["msg-id"] == "resub":
            user = tags["display-name"]
            self.bot.logger.info(f"{user} resubscribed to '{channel.name}'")
            await channel.send(f"Thanks for the {tags['msg-param-cumulative-months']}-month resub, @{user} - Welcome back! <3")


def prepare(bot):
    bot.add_cog(SubscriptionsCog(bot))
