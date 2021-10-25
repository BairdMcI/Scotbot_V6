import asyncio
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
import twitchio
import random


class Giveaway:
    def __init__(self, name: str, channelName: str, entrants=None, winners=None, isOpen: int = 1):
        self.name: str = name
        self.channelName: str = channelName
        self.entrants: list = [] if entrants is None else json.loads(entrants)
        self.winners: list = [] if winners is None else json.loads(winners)
        self.isOpen: bool = isOpen == 1

    def __str__(self):
        return self.name

    async def saveEntrants(self):
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            await db.execute("UPDATE giveaways SET entrants=? WHERE keyword = ?", (json.dumps(self.entrants), self.name,))
            await db.commit()

    async def saveEntrantsLoop(self):
        while self.isOpen:
            await self.saveEntrants()
            await asyncio.sleep(10)

    async def drawWinner(self):
        if len(self.entrants) == 0:
            return None
        else:
            winner = self.entrants.pop(random.randrange(0, len(self.entrants)))
            self.winners.append(winner)
            async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
                await db.execute("UPDATE giveaways SET winners=? WHERE keyword=?", (json.dumps(self.winners), self.name,))
                await db.execute("UPDATE giveaways SET entrants=? WHERE keyword = ?", (json.dumps(self.entrants), self.name,))
                await db.commit()
            return winner

    async def close(self):
        self.isOpen = False
        await self.saveEntrants()
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            await db.execute("UPDATE giveaways SET isOpen=0 WHERE keyword=?", (self.name,))
            await db.commit()

        return len(self.entrants) + len(self.winners)

    async def addToDB(self, channelName: str):
        async with aiosqlite.connect(f"data/{channelName}/{channelName}.db") as db:
            await db.execute("INSERT OR REPLACE INTO giveaways VALUES (?, '[]', '[]', 1)", (self.name,))
            await db.commit()


@dataclass
class SongRequest:
    requester: str
    song: str
    requestedAt: datetime
    channelName: str
    queuePosition: int = 1
    rowID: int = 0
    played: bool = False

    def __str__(self):
        return self.song

    async def addToDB(self):
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            cur = await db.execute("INSERT INTO songs VALUES (?, ?, ?, 0)", (self.requester, self.song, self.requestedAt.strftime("%d/%m/%Y %H:%M:%S"),))
            self.rowID = cur.lastrowid
            await db.commit()

    async def play(self):
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            await db.execute("UPDATE songs SET played=1 WHERE ROWID=?", (self.rowID,))
            await db.commit()
        self.played = True


class Poll:
    def __init__(self, options: dict, channelName: str, rowid: int = 0, voters=None, isOpen: bool = True):
        if voters is None:
            voters = []
        self.channelName: str = channelName
        self.options: dict = options
        self.voters: list = voters
        self.isOpen: bool = isOpen
        self.rowid: int = rowid

    async def addToDB(self):
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            print(self.options)
            cur = await db.execute("INSERT INTO polls VALUES (?, '[]', 1)", (json.dumps(self.options), ))
            await db.commit()
            self.rowid = cur.lastrowid
    
    async def updateDB(self):
        async with aiosqlite.connect(f"{self.channelName}/{self.channelName}.db") as db:
            await db.execute("UPDATE polls SET options=?, voters=?, isOpen=? WHERE ROWID=?",
                             (json.dumps(self.options), json.dumps(self.voters), 1 if self.isOpen else 0, self.rowid))
            await db.commit()
            
    async def updateLoop(self):
        while self.isOpen:
            await self.updateDB()
            await asyncio.sleep(30)


@dataclass
class Quote:
    user: str
    addUser: str
    quote: str
    submittedAt: datetime

    async def addToDB(self, channelName: str) -> Optional[int]:
        quoteCount = None
        async with aiosqlite.connect(f"data/{channelName}.db") as db:
            exists = await db.execute("SELECT 1 FROM quotes WHERE user=? AND userAdd=? AND text=?", (self.user, self.addUser, self.quote,))
            if not await exists.fetchone():
                await db.execute("INSERT INTO quotes VALUES (?, ?, ?, ?)", (self.user, self.addUser, self.quote, self.submittedAt.strftime("%d/%m/%Y %H:%M:%S")))
                cur = await db.execute("SELECT COUNT(*) FROM quotes")
                quoteCount = await cur.fetchone()
                quoteCount = quoteCount[0]
                await db.commit()
        return quoteCount


@dataclass
class Game:
    id: str
    name: str
    categories: str
    genres: str
    developers: str


class Channel:
    def __init__(self, name: str, id: int, webhookID: str, webhookToken: str, isLive: int):
        self.name: str = name
        self.id: int = id
        self.webhookID: str = webhookID
        self.webhookToken: str = webhookToken
        self.isLive: bool = isLive == 1

        self.poll: Optional[Poll] = None
        self.songs: list = []
        self.messages: list = []
        self.giveaways: dict = {}
        self.chatLogs: list = []

        self.channelObj: Optional[twitchio.Channel] = None

        self.setupTables()
        self.loadFromDB()

    def __str__(self):
        return self.name

    def setupTables(self):
        Path("data/"+self.name).mkdir(exist_ok=True)
        con = sqlite3.connect(f"data/{self.name}/{self.name}.db")
        con.execute("CREATE TABLE IF NOT EXISTS giveaways (keyword text unique primary key, entrants text, winners text, isOpen integer)")
        con.execute("CREATE TABLE IF NOT EXISTS polls (options text, voters text, isOpen integer)")
        con.execute("CREATE TABLE IF NOT EXISTS quotes (user text collate NOCASE, userAdd text collate NOCASE, quote text collate NOCASE , submittedAt text)")
        con.execute("CREATE TABLE IF NOT EXISTS whatgames (game text collate NOCASE, whatgame text)")
        con.execute("CREATE TABLE IF NOT EXISTS songs (requester text collate NOCASE, song text collate NOCASE, submittedAt text, played integer)")
        con.commit()
        con.close()
        con = sqlite3.connect(f"data/{self.name}/chatLogs.db")
        con.execute(f"CREATE TABLE IF NOT EXISTS {datetime.now().strftime('%B')} (date text, user text, message text)")
        con.commit()
        con.close()

    def loadFromDB(self):
        con = sqlite3.connect(f"data/{self.name}/{self.name}.db")
        data = con.execute("SELECT * FROM giveaways WHERE isOpen=1").fetchall()
        self.giveaways = {giveaway[0]: Giveaway(channelName=self.name, name=giveaway[0], entrants=giveaway[1], winners=giveaway[2]) for giveaway in data}

        data = con.execute("SELECT ROWID, options, voters FROM polls WHERE isOpen=1").fetchone()
        if data is not None:
            self.poll = Poll(options=json.loads(data[1]), voters=json.loads(data[2]), channelName=self.name, rowid=data[0])
        else:
            self.poll = None

        data = con.execute("SELECT ROWID, * FROM songs WHERE played=0").fetchall()
        if data is not None:
            self.songs = [SongRequest(requester=x[1], song=x[2], rowID=x[0], channelName=self.name, requestedAt=datetime.strptime(x[3], "%d/%m/%Y %H:%M:%S"), queuePosition=idx)
                          for idx, x in enumerate(data)]
        con.close()

    async def saveChatLogs(self):
        if len(self.chatLogs) > 0:
            async with aiosqlite.connect(f"data/{self.name}/chatLogs.db") as db:
                try:
                    await db.executemany(f"INSERT INTO {datetime.now().strftime('%B')} VALUES (?, ?, ?)", self.chatLogs)
                except sqlite3.OperationalError:
                    await db.execute(f"CREATE TABLE IF NOT EXISTS {datetime.now().strftime('%B')} (date text, user text, message text)")
                    await db.executemany(f"INSERT INTO {datetime.now().strftime('%B')} VALUES (?, ?, ?)", self.chatLogs)
                await db.commit()
            self.chatLogs = []

    async def saveChatLogsLoop(self):
        while True:
            await self.saveChatLogs()
            await asyncio.sleep(60)

    async def openGiveaway(self, keyword: str) -> Giveaway:
        giveaway = Giveaway(name=keyword, channelName=self.name)
        self.giveaways[keyword] = giveaway
        await giveaway.addToDB(self.name)

        return giveaway

    async def addQuote(self, user: str, userAdd: str, text: str, submittedAt: datetime) -> int:
        quote = Quote(user, userAdd, text, submittedAt)
        quoteCount = None
        if self.name in ["akiss4luck", "essentia_modica", "scotbotm8"]:
            names = ["akiss4luck", "essentia_modica", "scotbotm8"]
        else:
            names = [self.name]

        for name in names:
            quoteCount = await quote.addToDB(name)

        return quoteCount

    async def getQuote(self, searchTerm: Optional[str], quoteNum: Optional[int]) -> (Quote, int):
        async with aiosqlite.connect(f"data/{self.name}/{self.name}.db") as db:
            if searchTerm is None:
                cur = await db.execute("SELECT user, userAdd, quote, submittedAt FROM quotes")
                quotes = await cur.fetchall()
            else:
                cur = await db.execute("SELECT user, userAdd, quote, submittedAt FROM quotes WHERE user=? OR userAdd=? OR quote LIKE ?",
                                       (searchTerm, searchTerm, "%"+searchTerm+"%"))
                quotes = await cur.fetchall()
        quotes = [Quote(quote[0], quote[1], quote[2], datetime.strptime(quote[3], "%d/%m/%Y %H:%M:%S")) for quote in quotes]
        if quoteNum is None:
            quoteNum = random.randrange(0, len(quotes))
        else:
            quoteNum -= 1
        quote = quotes[quoteNum]

        return quote, quoteNum+1, len(quotes)

    async def addWhatgame(self, game: str, whatgame: str) -> bool:
        async with aiosqlite.connect(f"data/{self.name}/{self.name}.db") as db:
            exists = await db.execute("SELECT 1 FROM whatgames WHERE game=? AND whatgame=?", (game, whatgame, ))
            if not await exists.fetchone():
                await db.execute("INSERT INTO whatgames VALUES (?, ?)", (game, whatgame,))
                await db.commit()
                return True
            else:
                return False

    async def startPoll(self, options: list):
        self.poll = Poll({x: 0 for x in options}, self.name)
        await self.poll.addToDB()

    async def closePoll(self):
        self.poll.isOpen = False
        await self.poll.updateDB()
        self.poll = None

    async def addSong(self, user: str, song: str):
        newSong = SongRequest(requester=user, song=song, channelName=self.name, requestedAt=datetime.now())
        if newSong.song not in [song.song for song in self.songs]:
            self.songs.append(newSong)
            newSong.position = len(self.songs)
            await newSong.addToDB()
            return newSong.position
        else:
            return None

    async def getNextSong(self) -> Optional[SongRequest]:
        if len(self.songs) > 0:
            nextSong: SongRequest = self.songs.pop(0)
            await nextSong.play()
            return nextSong
        else:
            return None
