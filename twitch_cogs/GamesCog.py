import asyncio
from typing import Optional

import aiohttp
import aiosqlite
import pandas as pd
from requests.exceptions import SSLError
from twitchio.ext import commands

from twitchBot import Scotbot
from twitchClasses import Game


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    async def get_request(self, url, parameters=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, params=parameters) as response:
                    if response.status == 500:
                        return None
                    return await response.json()
        except SSLError as s:
            print('SSL Error:', s)

            for i in range(5, 0, -1):
                print('\rWaiting... ({})'.format(i), end='')
                await asyncio.sleep(1)
            print('\rRetrying.' + ' ' * 10)

            # recursively try again
            return await self.get_request(url, parameters)

    async def parse_steam_request(self, appid, name):
        url = "http://store.steampowered.com/api/appdetails/"
        parameters = {"appids": appid}
        json_data = await self.get_request(url, parameters)
        json_app_data = json_data[str(appid)]
        if json_app_data['success']:
            data = json_app_data['data']
        else:
            data = {'name': name, 'steam_appid': appid}
        return data

    async def updateGamesList(self):
        url = "https://steamspy.com/api.php"
        parameters = {"request": "all"}
        json_data = await self.get_request(url=url, parameters=parameters)
        steam_spy_all = pd.DataFrame.from_dict(json_data, orient='index')
        for x in range(1, 1000):
            parameters = {"request": "all", "page": x}
            json_data = await self.get_request(url=url, parameters=parameters)
            if json_data is None:
                break
            steam_spy_page = pd.DataFrame.from_dict(json_data, orient='index')
            steam_spy_all = steam_spy_all.append(steam_spy_page)
        app_list = steam_spy_all[['appid', 'name']].sort_values('appid').reset_index(drop=True)
        app_list.to_csv("data/app_list.csv", index=False)

        data = list(app_list.itertuples(index=False, name=None))

        async with aiosqlite.connect("data/generalTwitchInfo.db") as db:
            await db.executemany("INSERT OR REPLACE INTO gameIDs VALUES (?, ?)", data)
            await db.commit()

    async def fetchGame(self, gameName) -> Optional[Game]:
        async with aiosqlite.connect("generalTwitchInfo.db") as db:
            cur = await db.execute("SELECT * FROM gameInfo WHERE gameName LIKE ?", ("%"+gameName+"%",))
            data = await cur.fetchone()
        if data is not None:
            game: Game = Game(*data)
        else:
            async with aiosqlite.connect("data/generalTwitchInfo.db") as db:
                cur = await db.execute("SELECT * FROM gameIDs WHERE gameName LIKE ?", ("%"+gameName+"%",))
                data = await cur.fetchone()
                if data is None:
                    return None
                rawData = await self.parse_steam_request(*data)
                categories = " and ".join([category["description"] for category in rawData["categories"] if category["id"] in [1, 2]])
                genres = "-".join([genre["description"] for genre in rawData["genres"] if genre["id"] in ["1", "2", "3", "28", "9"]])
                developers = " and ".join(rawData["developers"])
                data = (data[0], data[1], categories, genres, developers,)
                await db.execute("INSERT INTO gameInfo VALUES(?, ?, ?, ?, ?)", data)
                await db.commit()
            game: Game = Game(*data)
        return game

    @commands.command(name="updateWhatgame")
    async def getGame(self, ctx: commands.Context):
        if ctx.channel.name == "deadm8":
            streamInfo = await self.bot.fetch_channel(ctx.channel.name)
            gameName = streamInfo.game_name
            game: Game = await self.fetchGame(gameName)
            if game is not None:
                await ctx.send(f"!editcom !whatgame DeadM8 is playing the {game.genres} {game.categories} game, {game.name}, developed by {game.developers}. | LINK: "
                               f"store.steampowered.com/app/{game.id}")
            else:
                await ctx.send(f"@{ctx.author.display_name}, no game with the name '{gameName}' could be found!")



def prepare(bot):
    bot.add_cog(GamesCog(bot))
