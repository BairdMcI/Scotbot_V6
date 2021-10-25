from twitchio.ext import commands
from rollFunctions import returnRoll
from twitchBot import Scotbot


class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context):
        diceMessage = await returnRoll(ctx.message.content)
        if diceMessage is None:
            await ctx.reply(f"I'm sorry I can't do that")
        elif len(diceMessage) > 1000:
            await ctx.reply(diceMessage.split('; ')[1])
        else:
            await ctx.reply(f"{ctx.author.display_name} rolled {diceMessage}")


def prepare(bot):
    bot.add_cog(DiceCog(bot))
