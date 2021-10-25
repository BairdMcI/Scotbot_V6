from twitchio.ext import commands
from rollFunctions import returnRoll


class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx):
        diceMessage = await returnRoll(ctx.message.content)
        if diceMessage is None:
            await ctx.send(f"I'm sorry @{ctx.author.display_name}, I can't do that")
        elif len(diceMessage) > 1000:
            await ctx.send(f"@{ctx.author.display_name}, {diceMessage.split('; ')[1]}")
        else:
            await ctx.send(f"@{ctx.author.display_name} rolled {diceMessage}")


def prepare(bot):
    bot.add_cog(DiceCog(bot))
