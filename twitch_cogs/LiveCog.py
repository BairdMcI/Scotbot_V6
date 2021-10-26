from datetime import datetime

from twitchio import models
from twitchio.ext import commands
from twitchio.ext.routines import routine

from twitchBot import Scotbot
from twitchClasses import Channel


class LiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="isLive")
    async def isLive(self, ctx: commands.Context):
        channel: Channel = self.bot.channels[ctx.channel.name]
        if await self.checkIfLive(channel):
            await ctx.reply(f"The channel is live just now! Playing: {channel.game}")
        else:
            await ctx.reply(f"{channel.displayName} is not live just now")

    async def checkIfLive(self, channel: Channel) -> bool:
        streamInfo: list[models.Stream] = await self.bot.fetch_streams(user_logins=[channel.name])
        onlineCode = await channel.checkIfLive(streamInfo)
        if onlineCode[1]:
            self.bot.logger.info(f"{channel.name} updated their title to: {channel.title}")
        if onlineCode[2]:
            rawData = await self.bot.fetch_games(names=[channel.game])
            try:
                gameInfo: models.Game = rawData[0]
                channel.gameImageURL = gameInfo.art_url(1000, 1000)
            except IndexError:
                channel.gameImageURL = ""

            self.bot.logger.info(f"{channel.name} updated their game to: {channel.game}")
            if onlineCode[0] == 1:
                await channel.sendWebhook(changedGames=True)
        if onlineCode[0] == 2:
            self.bot.logger.info(f"{channel.name} went online")
            await channel.sendWebhook(changedGames=False)

        elif onlineCode[0] == -2:
            self.bot.logger.info(f"{channel.name} went offline")
        return True if onlineCode[0] > 0 else False

    @routine(minutes=5)
    async def checkIfLiveRoutine(self):
        for channel in self.bot.channels.values():
            await self.checkIfLive(channel)


def prepare(bot):
    bot.add_cog(LiveCog(bot))