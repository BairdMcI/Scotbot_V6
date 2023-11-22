import logging
import logger as _logger
from discord.ext import commands

from rollFunctions import returnRoll
LOGGER = logging.getLogger(__name__)
_logger.setupLogger(LOGGER)


class ExtraCommands(commands.Cog):
    """Miscellaneous / Extra Commands"""
    def __init__(self, bot):
        self._bot = bot

    @commands.command(name="scotbotTest")
    async def scotbotTest(self, ctx):
        await ctx.send(f"Version 6 of me is alive and well!")
        LOGGER.info(f"{ctx.message.guild} | {ctx.message.channel} | {ctx.author.name} used '!scotbotTest'")

    @commands.command(name="barrelRoll")
    async def barrelRoll(self, ctx):
        await ctx.send("https://tenor.com/view/barrel-roll-panda-barrelroll-funny-gif-4935160")

    @commands.command(name="dammit")
    async def dammit(self, ctx):
        try:
            await ctx.send(f"I blame {ctx.message.content.split('dammit ')[1]}. 'cause reasons!")
        except IndexError:
            await ctx.send(f"Plz type in something to blame...")
        LOGGER.info(f"{ctx.message.guild} | {ctx.message.channel} | {ctx.author.name} used '!dammit'")


def setup(bot):
    bot.add_cog(ExtraCommands(bot))
