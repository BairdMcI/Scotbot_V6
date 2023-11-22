import asyncio
import json
from typing import Optional

import aiosqlite

heartList = [u"\U0001F496", u"\U0001F49B", u"\U0001F499", u"\U0001F49A"	, u"\U0001F49C", u"\U0001F493",	u"\U0001F90D", 	u"\U0001F90E", 	u"\U0001F9E1", u"\U0001F5A4"]
presenceList = ["Bin Weevils \U0001F3AE", "Chess... against itself \u265A", "Human Simulator 2020 \U0001F3AE", "with it's drink \U0001F943",
                "World Domination Platinum Edition \U0001F310", "you like a fiddle \U0001F3BB", "hide and seek \U0001F3C3", "the fiddle in an irish band \U0001F3BB"]
quillRoleAssignment = {"quillYetu": 651408409652101120, "quillScience": 656217581816119326, "quillDove": 706466749457104936}
mainChannels = {"Lucky Alliance": 290576301688094721, "Quill18": 651856272723017729, "Tooth and Tale": 327848930542878730,
                 "Scotbot Haggis Hill": 442377812708556813}

avatarURL = "https://cdn.discordapp.com/attachments/176727246160134144/491033960877391892/ScotBot5Shadow.png"


class ServerClass:
    def __init__(self, name: str, serverID=None):
        self.name: str = name
        self.serverID: int = serverID
        self.modRole: Optional[int] = None
        self.chats: dict = {}
        self.giveaways: dict = {}

    async def saveChatLogs(self):
        while True:
            if len(self.chats) > 0:
                async with aiosqlite.connect(f"data/discord/{self.name}.db") as db:
                    await db.executemany(f"INSERT INTO chatlogs VALUES (?, ?, ?)", self.chats)
                    await db.commit()
                self.chats = {}
            await asyncio.sleep(300)

    async def initialLoad(self):
        async with aiosqlite.connect(f"data/discord/{self.name}.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS chatlogs (date text, user text COLLATE NOCASE, message text COLLATE NOCASE)")
            await db.execute("CREATE TABLE IF NOT EXISTS giveaways (channelID integer, messageID integer primary key unique, entrants text, winners text, isOpen integer)")
            await db.commit()

        async with aiosqlite.connect("data/discord/generalDiscordInfo.db") as db:
            await db.execute("INSERT OR IGNORE INTO channelInfo(serverID) VALUES (?)", (self.serverID, ))
            await db.execute("UPDATE channelInfo SET serverName=? WHERE serverID=?", (self.name, self.serverID,))
            await db.commit()

    async def fetchModRole(self):
        async with aiosqlite.connect(f"data/discord/generalDiscordInfo.db") as db:
            cur = await db.execute("SELECT modRole FROM channelInfo WHERE serverID=?", (self.serverID,))
            data = await cur.fetchone()
            if data is not None:
                data = data[0]
            self.modRole = data

    async def saveGiveaways(self):
        async with aiosqlite.connect(f"data/discord/{self.name}.db") as db:
            for channelID, (messageID, entrants, winners) in self.giveaways.items():
                await db.execute(f"INSERT OR REPLACE INTO giveaways VALUES (?, ?, ?, ?, ?)", (channelID, messageID, json.dumps(entrants), json.dumps(winners), 1))
                await db.commit()

    async def fetchGiveaways(self):
        async with aiosqlite.connect(f"data/discord/{self.name}.db") as db:
            cur = await db.execute(f"SELECT * FROM giveaways WHERE isOpen=1")
            data = await cur.fetchall()
        for (channelID, messageID, entrants, winners, isOpen) in data:
            self.giveaways[channelID] = [messageID, json.loads(entrants), json.loads(winners)]

    async def closeGiveaway(self, messageID: int, channelID: int):
        async with aiosqlite.connect(f"data/discord/{self.name}.db") as db:
            await db.execute("UPDATE giveaways SET isOpen=0 WHERE messageID=?", (messageID,))
            await db.commit()
        del self.giveaways[channelID]




