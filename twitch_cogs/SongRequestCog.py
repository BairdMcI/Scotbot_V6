from twitchio.ext import commands

from twitchBot import Scotbot, requireMod
from twitchClasses import Channel, SongRequest


class SongRequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @commands.command(name="openRequests")
    @requireMod
    async def openRequests(self, ctx: commands.Context):
        if ctx.author.is_mod and ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            if not channel.requestsOpen:
                channel.requestsOpen = True
                await ctx.reply("Requests are now open!")
            else:
                await ctx.reply("Requests are already open!")

    @commands.command(name="closeRequests")
    @requireMod
    async def closeRequests(self, ctx: commands.Context):
        if ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            if channel.requestsOpen:
                channel.requestsOpen = False
                await ctx.reply("Requests are now closed!")
            else:
                await ctx.reply("Requests are already closed!")

    @commands.command(name="songRequest", aliases=["sr"])
    async def requestSong(self, ctx: commands.Context, *args):
        if ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            if not channel.requestsOpen:
                await ctx.send("Requests aren't open just now!")
                return
            songData = " ".join(args)
            if len(songData) < 5:
                await ctx.reply("Please give something to search for!")
                return
            songPosition = await channel.addSong(ctx.author.display_name, songData)
            if songPosition is not None:
                await ctx.reply(f"{songData} has been added to the request queue! Position: {songPosition}")
            else:
                await ctx.reply(f"The song {songData} is already in the queue!")

    @commands.command(name="nextSong")
    @requireMod
    async def getNextSong(self, ctx: commands.Context):
        if ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            nextSong: SongRequest = await channel.getNextSong()
            if nextSong is None:
                await ctx.reply("There are no songs in the Request Queue!")
            else:
                await ctx.reply(f"Next song: {nextSong.song}; requested by {nextSong.requester}. Possible link: https://chorus.fightthe.pw/search?query="
                                f"{nextSong.song.replace(' ', '%20')}")

    @commands.command(name="songQueue")
    async def getSongQueue(self, ctx: commands.Context):
        if ctx.channel.name == "deadm8":
            channel: Channel = self.bot.channels[ctx.channel.name]
            songList: list[SongRequest] = channel.songs
            if len(songList) > 0:
                output = songList[0].song
                songNumber = 1
                while (len(output) + len(songList[songNumber].song)) <= 450 and songNumber < len(songList):
                    output = f"{output}; {songList[songNumber].song}"
                    songNumber += 1
                if songNumber == len(songList):
                    await ctx.reply(f"Current songs in the queue: {output}")
                else:
                    await ctx.reply(f"First {songNumber} song(s) in the song Queue. Total Number of Songs: {len(songList)}")
            else:
                await ctx.reply("There are no songs in the Request Queue!")


def prepare(bot):
    bot.add_cog(SongRequestCog(bot))
