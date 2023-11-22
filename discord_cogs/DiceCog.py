import logging
import logger as _logger
from discord.ext import commands

from rollFunctions import returnRoll
LOGGER = logging.getLogger(__name__)
_logger.setupLogger(LOGGER)


class RollsCog(commands.Cog):
    """Dice Cog"""
    def __init__(self, bot):
        self._bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context):
        async with ctx.channel.typing():
            diceMessage = await returnRoll(ctx.message.content)
            if diceMessage is None:
                await ctx.send(f"I'm sorry {ctx.author.mention}, I can't do that")
            elif len(diceMessage) > 1000:
                await ctx.send(f"{ctx.author.mention}, {diceMessage.split('; ')[1]}")
            else:
                await ctx.send(f"{ctx.author.mention} rolled {diceMessage}")
            return


def setup(bot):
    bot.add_cog(RollsCog(bot))
