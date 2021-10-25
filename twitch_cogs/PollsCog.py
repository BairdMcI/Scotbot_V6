from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel


class PollsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="pollOpen")
    async def openPoll(self, ctx: commands.Context, *args):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            if channel.poll is None:
                rawData = " ".join(args)
                pollOptions = [option.strip() for option in rawData.split("|")]
                options = [f"{idx + 1}: {option}" for idx, option in enumerate(pollOptions)]
                await channel.startPoll(pollOptions)
                self.bot.loop.create_task(channel.poll.updateLoop())
                await ctx.reply(f"A poll has been opened! Options: {'; '.join(options)}. To enter, type '!vote 1' to vote for option 1, !vote 2 for option 2 etc")
            else:
                await ctx.reply(f"There is already a poll open! Please close it first")

    @commands.command(name="vote")
    async def vote(self, ctx: commands.Context, *args):
        channel: Channel = self.bot.channels[ctx.channel.name]
        if channel.poll is not None:
            if ctx.author.name not in channel.poll.voters:
                try:
                    option = int(args[0])
                except ValueError:
                    return
                channel.poll.options[list(channel.poll.options.keys())[option - 1]] += 1
                channel.poll.voters.append(ctx.author.name)

    @commands.command(name="pollVotes")
    async def pollVotes(self, ctx: commands.Context):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            if channel.poll is not None:
                options = [f"{key}: {value}" for key, value in channel.poll.options.items()]
                await channel.poll.updateDB()
                await ctx.reply(f"Results of the poll so far: {'; '.join(options)}")
            else:
                await ctx.reply(f"There is no poll open just now!")

    @commands.command(name="pollClose")
    async def pollClose(self, ctx: commands.Context):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            if channel.poll is not None:
                options = [f"{key}: {value}" for key, value in channel.poll.options.items()]
                await ctx.reply(f"The poll has been closed! Results: {'; '.join(options)}")
                await channel.closePoll()
            else:
                await ctx.reply(f"There is no poll open just now!")


def prepare(bot):
    bot.add_cog(PollsCog(bot))
