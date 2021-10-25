from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Channel, SongRequest


class SongRequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="openRequests")
    async def openRequests(self, ctx: commands.Context):
        if ctx.author.is_mod and ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            if not channel.requestsOpen:
                channel.requestsOpen = True
                await ctx.reply("Requests are now open!")
            else:
                await ctx.reply("Requests are already open!")

    @commands.command(name="songRequest")
    async def requestSong(self, ctx: commands.Context, *args):
        if ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            songData = " ".join(args)
            songPosition = await channel.addSong(ctx.author.display_name, songData)
            if songPosition is not None:
                await ctx.reply(f"{songData} has been added to the request queue! Position: {songPosition}")
            else:
                await ctx.reply(f"The song {songData} is already in the queue!")

    @commands.command(name="nextSong")
    async def getNextSong(self, ctx: commands.Context):
        if ctx.channel.name == "deadm8" and ctx.author.is_mod:
            channel: Channel = self.bot.channels[ctx.channel.name]
            nextSong: SongRequest = await channel.getNextSong()
            if nextSong is None:
                await ctx.reply("There are no songs in the Request Queue!")
            else:
                await ctx.reply(f"Next song: {nextSong.song}; requested by {nextSong.requester}. Possible link: https://chorus.fightthe.pw/search?query="
                                f"{nextSong.song.replace(' ', '%20')}")


def prepare(bot):
    bot.add_cog(SongRequestCog(bot))
