from datetime import datetime, timedelta
from typing import Optional

from twitchio import models
from twitchio.ext import commands
from twitchio.ext.routines import routine

from twitchBot import Scotbot
from twitchClasses import Channel, Game


class LiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="isLive")
    async def isLive(self, ctx: commands.Context):
        channel: Channel = self.bot.channels[ctx.channel.name]
        if await self.checkIfLive([channel.name]) is not None:
            await ctx.reply(f"The channel is live just now! Playing: {channel.game}")
        else:
            await ctx.reply(f"{channel.displayName} is not live just now")

    async def checkIfLive(self, channels: list[str]) -> Optional[dict]:
        streamInfoList: list[models.Stream] = await self.bot.fetch_streams(user_logins=channels)
        if len(streamInfoList) == 0:
            return None
        return {streamInfo.user.id: streamInfo for streamInfo in streamInfoList}

    async def getGame(self, gameName: str, gameID: int) -> Game:
        rawData = await self.bot.fetch_games(ids=[gameID])
        try:
            gameInfo: models.Game = rawData[0]
            return Game(name=gameName, id=gameID, image=gameInfo.art_url(1000, 1000))
        except IndexError:
            return Game(name=gameName, id=gameID)

    @routine(minutes=1)
    async def checkIfLiveRoutine(self):
        streamInfoList: dict[id: models.Stream] = await self.checkIfLive(self.bot.channels.keys())
        if streamInfoList is not None:
            for channel in self.bot.channels.values():
                if channel.id in streamInfoList:
                    streamInfo = streamInfoList[channel.id]
                    if not channel.isLive and channel.lastOnline < (datetime.now() - timedelta(hours=2)):  # Channel has just gone live
                        self.bot.logger.info(f"{channel.displayName} has gone live! Playing {channel.game.name}")
                        channel.game = await self.getGame(streamInfo.game_name, streamInfo.game_id)
                        channel.title = streamInfo.title
                        channel.lastOnline = datetime.now()
                        channel.isLive = True
                        await channel.updateStreamInfo(game=True, title=True, isLive=True, lastOnline=True)
                        await channel.sendWebhook(changedGames=False)
                        self.bot.logger.info(f"{channel.displayName} - Gone live notification sent")
                        self.bot.cogs.get("ExtraCommandsCog").whatgameRoutine.start(channel.name)
                        if channel.name == "deadm8":
                            await self.bot.cogs.get("GamesCog").updateWhatgame(channel.name)

                    elif channel.game.name != streamInfo.game_name:
                        self.bot.logger.info(f"{channel.displayName} has changed their game to {streamInfo.game_name}")
                        channel.game = await self.getGame(streamInfo.game_name, streamInfo.game_id)
                        channel.title = streamInfo.title
                        channel.lastOnline = datetime.now()
                        channel.isLive = True
                        await channel.updateStreamInfo(game=True, lastOnline=True, title=True)
                        await channel.sendWebhook(changedGames=True)
                        self.bot.logger.info(f"{channel.displayName} - Game change notification sent")
                        self.bot.cogs.get("ExtraCommandsCog").whatgameRoutine.start(channel.name)
                    else:
                        channel.lastOnline = datetime.now()
                        if not channel.isLive:
                            channel.isLive = True
                        await channel.updateStreamInfo(isLive=True, lastOnline=True)

                else:
                    if channel.isLive:  # Channel has just gone offline
                        channel.isLive = False
                        self.bot.logger.info(f"{channel.displayName} has just gone offline")
                        await channel.updateStreamInfo(isLive=True)
                        VODs: models.Video = await self.bot.fetch_videos(user_id=channel.id)
                        await channel.sendVOD(VODs[0])
                # else:
                #     if channel.lastOnline < (datetime.now() - timedelta(minutes=30)):
                #         await channel.sendVOD()
                # Send VOD
            # self.bot.logger.info(f"{channel.displayName}: Title: {channel.title}, playing {channel.game.name}. Last online: "
            #                      f"{'Now!' if channel.isLive else channel.lastOnline.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            for channel in self.bot.channels.values():
                if channel.isLive:  # Channel has just gone offline
                    channel.isLive = False
                    self.bot.logger.info(f"{channel.displayName} has just gone offline")
                    await channel.updateStreamInfo(isLive=True)

    @checkIfLiveRoutine.before_routine
    async def initialCheck(self):
        streamInfoList: dict[id: models.Stream] = await self.checkIfLive(self.bot.channels.keys())
        if streamInfoList is None:
            for channel in self.bot.channels.values():
                channel.isLive = False
                await channel.updateStreamInfo(isLive=True)
        else:
            for channel in self.bot.channels.values():
                if channel.id in streamInfoList:
                    streamInfo: models.Stream = streamInfoList[channel.id]
                    channel.game = await self.getGame(streamInfo.game_name, streamInfo.game_id)
                    channel.title = streamInfo.title
                    channel.lastOnline = datetime.now()
                    channel.isLive = True
                    await channel.updateStreamInfo(game=True, title=True, isLive=True, lastOnline=True)
                else:
                    channel.isLive = False
                    await channel.updateStreamInfo(isLive=True)


def prepare(bot):
    bot.add_cog(LiveCog(bot))
