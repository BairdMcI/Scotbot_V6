import asyncio

from twitchio import models, Message
from twitchio.ext import commands, routines

from twitchBot import Scotbot
from twitchClasses import Channel


class ExtraCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="whatgame")
    async def parseWhatgame(self, ctx: commands.Context):
        await self.whatgame(ctx.channel.name)

    @routines.routine(minutes=10, iterations=1)
    async def whatgameRoutine(self, channelName: str):
        channel: Channel = self.bot.channels[channelName]
        await channel.channelObj.send("!whatgame")
        await self.whatgame(channelName)

    async def whatgame(self, channelName: str):
        def checkIfBot(message: Message):
            if message.author is not None:
                return message.author.name in ["nightbot", "moobot"]
            return False

        try:
            response = await self.bot.wait_for(event="message", predicate=checkIfBot, timeout=10)
        except asyncio.TimeoutError:
            return
        streamInfo: models.Stream = await self.bot.fetch_channel(channelName)

        channel: Channel = self.bot.channels[channelName]
        status = await channel.addWhatgame(game=streamInfo.game_name, title=streamInfo.title, whatgame=response[0].content)
        if status:
            self.bot.logger.info(f"Added whatgame for {channel.name} for game '{streamInfo.game_name}'")

    @commands.command(name="scotbotTest")
    async def scotbotTest(self, ctx: commands.Context):
        await ctx.reply("Scotbot V6 is kind of here!")

    @commands.command(name="dammit")
    async def dammitCommand(self, ctx: commands.Context, *args, message):
        await ctx.reply(f"I blame {message}. Cause reasons!")


def prepare(bot):
    bot.add_cog(ExtraCommandsCog(bot))
