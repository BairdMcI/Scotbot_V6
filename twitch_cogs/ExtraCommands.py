import asyncio

from twitchio import models, Message
from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel


class ExtraCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="whatgame")
    async def whatgame(self, ctx: commands.Context):
        def checkIfBot(message: Message):
            return message.author.name in ["nightbot", "moobot"]

        try:
            response = await self.bot.wait_for(event="message", predicate=checkIfBot, timeout=10)
        except asyncio.TimeoutError:
            return
        channel: Channel = self.bot.channels[ctx.channel.name]
        streamInfo: models.Stream = await self.bot.fetch_channel(channel.name)
        status = await channel.addWhatgame(game=streamInfo.game_name, title=streamInfo.title, whatgame=response[0].content)
        if status:
            self.bot.logger.info(f"Added whatgame for {channel.name} for game '{streamInfo.game_name}'")

    @commands.command(name="scotbotTest")
    async def scotbotTest(self, ctx: commands.Context):
        await ctx.reply("Scotbot V6 is kind of here!")

def prepare(bot):
    bot.add_cog(ExtraCommandsCog(bot))
