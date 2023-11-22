from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel, Giveaway

from discord import Webhook, RequestsWebhookAdapter, Embed, Colour


class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="giveawayOpen")
    async def openGiveaway(self, ctx: commands.Context, keyword: str):
        if ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            followersOnly = False
            subscribersOnly = False
            params = ctx.message.content.split(keyword)[1]
            for param in params.split(" "):
                if len(param) == 0:
                    continue
                param = param.lower()
                if not param.startswith("-"):
                    await ctx.reply("Please start your parameters with a hyphen!")
                    return
                if param not in ["-followers", "-subscribers"]:
                    await ctx.reply("Currently, the only valid parameters are: '-followers' and '-subscribers'")
                    return
                if param == "-followers":
                    followersOnly = True
                if param == "-subscribers":
                    subscribersOnly = True
            keyword = keyword.lower()
            if keyword not in [*channel.giveaways]:
                giveaway: Giveaway = await channel.openGiveaway(keyword, followersOnly, subscribersOnly)
                message = f"EVERYONE, a giveaway has been opened! To enter, type '{keyword}' into chat!"
                if followersOnly and subscribersOnly:
                    messageParams = "NOTE: This giveaway is only open to followers and subscribers"
                elif followersOnly:
                    messageParams = "NOTE: This giveaway is only open to followers"
                elif subscribersOnly:
                    messageParams = "NOTE: This giveaway is only open to subscribers"
                else:
                    messageParams = ""
                await ctx.reply(f"{message} {messageParams}")
                self.bot.logger.info(f"{message} {messageParams}")
                #self.bot.loop.create_task(giveaway.saveEntrantsLoop())
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
                    webhook = Webhook.partial(1085620106266157057, "G2jCFhMO1wVljumJYRljMkg_KjmTn_tRqQJ-LoXkjD0W4b867Ak9baFk_whMxsaVQ0e6", adapter=RequestsWebhookAdapter())
                    webhook.send(content=f"{winner} won the giveaway with the keyword '{keyword}'")
                    user = self.bot.create_user(int(self.bot.user_id), self.bot.nick)
                    await user.send_whisper(self.bot._http.token, ctx.author.id, "{winner} won the giveaway with the keyword '{keyword}'")
                    #await ctx.author.send(f"{winner} won the giveaway with the keyword '{keyword}'")
                    self.bot.logger.info(f"{winner} won the giveaway with the keyword {keyword}")
                else:
                    await ctx.reply(f"There could be no winner selected for the giveaway '{keyword}' as there were no entrants left!")
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
