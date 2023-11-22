import json

import aiohttp
import requests

import aiosqlite
from discord.http import Route
from twitchio.ext import commands
from twitchio.ext.routines import routine

from auth import twitchClientID, twitchClientSecret
from twitchBot import Scotbot, get_session
from twitchClasses import Channel


class SubmissionCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @routine(seconds=5)
    async def checkIfSubmission(self):
        async with aiosqlite.connect("data/generalTwitchInfo.db") as db:
            data = await db.execute("SELECT COUNT(*) FROM submissionQueue")
            if await data.fetchone():
                data = await db.execute("SELECT * FROM submissionQueue")
                data = await data.fetchall()
                for channelName, commandName, content in data:
                    await self.sendCommand(channelName, commandName, content)
                await db.execute("DELETE FROM submissionQueue")
                await db.commit()

    async def sendCommand(self, channelName: str, commandName: str, content: str):
        channel: Channel = self.bot.channels[channelName]
        if commandName == "whatgame":
            if channel.name == "quill18":
                await channel.channelObj.send(f"!whatgame {content}")
            else:
                await channel.channelObj.send(f"!editcom !whatgame {content}")
        elif commandName == "title":
            sess = get_session(client_id=twitchClientID, client_secret=twitchClientSecret, channelName=channelName, redirect_uri="https://example.com")
            url = "https://api.twitch.tv/helix/channels"
            headers = {"Authorization": f"Bearer {sess.token['access_token']}",
                       "client-id": twitchClientID}
            params = {"title": content, "broadcaster_id": str(channel.id)}
            print(url, headers, params)
            response = requests.patch(url, headers=headers, params=params)
            if response.status_code != 204:
                await channel.channelObj.send(f"!title {content}")
        elif commandName == "game":
            await channel.channelObj.send(f"!game {content}")

    @commands.command(name="testTitle")
    async def testTitle(self, ctx: commands.Context, *, content):
        if ctx.channel.name in ["deadm8", "scotbotm8"]:
            await self.sendCommand(ctx.channel.name, "title", content)
        # sess = get_session(self.bot._http.client_id, self.bot._http.client_secret, "https://localhost", ctx.channel.name)
        # print(sess.token["access_token"])
        # await self.bot._http.patch_channel(token=sess.token["access_token"], broadcaster_id=str(channel.id), title=content)

def prepare(bot):
    bot.add_cog(SubmissionCog(bot))
