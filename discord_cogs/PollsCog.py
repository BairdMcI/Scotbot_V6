import asyncio

from discord.ext import commands

from discordBot import Scotbot
from discordClasses import heartList


class PollsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="pollOpen")
    async def pollOpen(self, ctx: commands.Context):
        if await self.bot.checkIfMod(ctx):
            pollOptions = ctx.message.content.split("pollOpen ")[1].split("|")
            pollOptions = [option.strip() for option in pollOptions]
            outputMessage = "\n".join([f'{option} = {heartList[idx]}' for idx, option in enumerate(pollOptions)])
            outputMessage = await ctx.send(f"A poll has been opened! Click the corresponding heart! Options:\n{outputMessage}")
            for idx, option in enumerate(pollOptions):
                await outputMessage.add_reaction(emoji=heartList[idx])
            await outputMessage.pin()
            await asyncio.sleep(3600)
            await outputMessage.unpin()


def setup(bot):
    bot.add_cog(PollsCog(bot))
