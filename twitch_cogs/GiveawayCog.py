from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel, Giveaway


class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="giveawayOpen")
    async def openGiveaway(self, ctx: commands.Context, keyword: str):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            keyword = keyword.lower()
            if keyword not in [*channel.giveaways]:
                giveaway: Giveaway = await channel.openGiveaway(keyword)
                await ctx.reply(f"EVERYONE, a giveaway has been opened! To enter, type '{keyword}' into chat!")
                self.bot.logger.info(f"{ctx.author.display_name} opened a giveaway with the keyword {keyword}")
                self.bot.loop.create_task(giveaway.saveEntrantsLoop())
            else:
                await ctx.reply(f"A giveaway is already open with the keyword '{keyword}'. Please close it first!")

    @commands.command(name="giveawayDraw")
    async def drawGiveaway(self, ctx: commands.Context, keyword: str):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            keyword = keyword.lower()
            if keyword not in [*channel.giveaways]:
                await ctx.reply(f"There is no giveaway open with the keyword '{keyword}'!")
            else:
                giveaway: Giveaway = channel.giveaways[keyword]
                winner = await giveaway.drawWinner()
                if winner is not None:
                    await ctx.author.send(f"{winner} won the giveaway with the keyword '{keyword}'")
                    self.bot.logger.info(f"{winner} won the giveaway with the keyword {keyword}")
                else:
                    await ctx.author.reply(f"There could be no winner selected for the giveaway '{keyword}' as there were no entrants left!")
                    self.bot.logger.error(f"There were no entrants in the giveaway {keyword}")

    @commands.command(name="giveawayClose")
    async def closeGiveaway(self, ctx: commands.Context, keyword: str):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            keyword = keyword.lower()
            if keyword not in [*channel.giveaways]:
                await ctx.reply(f"There is no giveaway open with the keyword '{keyword}' to close!")
            else:
                giveaway: Giveaway = channel.giveaways[keyword]
                numEntrants = await giveaway.close()
                del channel.giveaways[keyword]
                await ctx.reply(f"The giveaway '{keyword}' has been closed! Thank you to the {numEntrants} that entered!")
                self.bot.logger.info(f"The giveaway {keyword} has been closed")


def prepare(bot):
    bot.add_cog(GiveawayCog(bot))
