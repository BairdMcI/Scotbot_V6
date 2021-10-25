import re
from datetime import datetime

from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel


class QuotesCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="addQuote")
    async def addQuote(self, ctx: commands.Context, *args):
        rawData = " ".join(args)
        channel: Channel = self.bot.channels[ctx.channel.name]
        user = re.search("<(.*)>", args[0])
        if user is None:
            await ctx.send(f"@{ctx.author.display_name}, please enclose the person who said the quote at the start of the quote in < > brackets!")
            return
        quote = rawData.split(">")[1].strip(" ")
        userAddDisplay = ctx.author.display_name
        submittedAt = datetime.now()
        quoteNum = await channel.addQuote(submittedAt, userAddDisplay, quote)
        if quoteNum is not None:
            self.bot.logger.info(f"{channel.name} | Quote from {userAddDisplay} added!")
            await ctx.send(f"@{ctx.author.display_name}, quote has been added to the database! Quote number: {quoteNum}")

    @commands.command(name="quote")
    async def getQuote(self, ctx: commands.Context, *args):
        channel: Channel = self.bot.channels[ctx.channel.name]
        if len(args) == 0:
            searchTerm = None
            quoteNum = None
        elif len(args) == 1:
            try:
                quoteNum = int(args[0])
                searchTerm = None
            except ValueError:
                quoteNum = None
                searchTerm = args[0]
        elif len(args) == 2:
            try:
                quoteNum = int(args[0])
                searchTerm = args[1]
            except ValueError:
                try:
                    quoteNum = int(args[1])
                    searchTerm = args[0]
                except ValueError:
                    pass
        else:
            try:
                quoteNum = int(args[-1])
                searchTerm = " ".join(args[:-1])
            except ValueError:
                pass

        quote, quoteNum, totalQuotes = await channel.getQuote(searchTerm, quoteNum)
        await ctx.send(f"<{quote.userDisplay}> {quote.quoteDisplay} | Submitted By: {quote.addUserDisplay} | ({quoteNum}/{totalQuotes})")


def prepare(bot):
    bot.add_cog(QuotesCog(bot))
