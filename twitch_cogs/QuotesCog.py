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
        channel: Channel = self.bot.channels[ctx.channel.name]
        print("Got here")
        if ctx.message.tags.get("reply-parent-msg-body") is not None:
            quote = f"<{ctx.message.tags['reply-parent-display-name']}> {ctx.message.tags['reply-parent-msg-body']}"
        else:
            rawData = " ".join(args)
            user = re.search("<(.*)>", args[0])
            if user is None:
                await ctx.reply(f"@{ctx.author.display_name}, please enclose the person who said the quote at the start of the quote in < > brackets!")
                return
            quote = rawData
        quoteNum = await channel.addQuote(datetime.now(), ctx.author.display_name, quote)

        if quoteNum is not None:
            self.bot.logger.info(f"{channel.name} | Quote from {ctx.author.display_name} added: {quote}")
            await ctx.reply(f"Quote has been added to the database! Quote number: {quoteNum}")

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

        quoteData = await channel.getQuote(searchTerm, quoteNum)
        if quoteData is None:
            await ctx.reply(f"No quotes for the term {searchTerm} could be found!")
        else:
            quote, quoteNum, totalQuotes = quoteData
            await ctx.reply(f"{quote.quote} | Submitted By: {quote.submitter} | ({quoteNum}/{totalQuotes})")


def prepare(bot):
    bot.add_cog(QuotesCog(bot))
