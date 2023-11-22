import asyncio
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
import twitchio
import random

from twitchio import models
from twitchio.ext import routines
from discord import Webhook, RequestsWebhookAdapter, Embed, Colour

botImage = "https://cdn.discordapp.com/attachments/176727246160134144/491033960877391892/ScotBot5Shadow.png"


class Giveaway:
    def __init__(self, name: str, channelName: str, entrants=None, winners=None, isOpen: int = 1, followersOnly: bool = False,
                 subscribersOnly: bool = False):
        self.name: str = name
        self.channelName: str = channelName
        self.entrants: list = [] if entrants is None else json.loads(entrants)
        self.winners: list = [] if winners is None else json.loads(winners)
        self.isOpen: bool = isOpen == 1
        self.followersOnly: bool = followersOnly
        self.subscribersOnly: bool = subscribersOnly

    def __str__(self):
        return self.name

    async def open(self):
        self.isOpen = True
        self.saveEntrants.start()

    @routines.routine(seconds=10)
    async def saveEntrants(self):
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            await db.execute("UPDATE giveaways SET entrants=? WHERE keyword = ?", (json.dumps(self.entrants), self.name,))
            await db.commit()

    @saveEntrants.after_routine
    async def finalSave(self):
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            await db.execute("UPDATE giveaways SET entrants=? WHERE keyword = ?", (json.dumps(self.entrants), self.name,))
            await db.commit()

    async def drawWinner(self):
        if len(self.entrants) == 0:
            return None
        else:
            winner = self.entrants.pop(random.randrange(0, len(self.entrants)))
            self.winners.append(winner)
            async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
                await db.execute("UPDATE giveaways SET winners=? WHERE keyword=?", (json.dumps(self.winners), self.name,))
                await db.execute("UPDATE giveaways SET entrants=? WHERE keyword = ?", (json.dumps(self.entrants), self.name,))
                await db.commit()
            return winner

    async def close(self):
        self.isOpen = False
        self.saveEntrants.stop()
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            await db.execute("UPDATE giveaways SET isOpen=0 WHERE keyword=?", (self.name,))
            await db.commit()
        return len(self.entrants) + len(self.winners)

    async def addToDB(self, channelName: str):
        async with aiosqlite.connect(f"data/user_{channelName}.db") as db:
            await db.execute("INSERT OR REPLACE INTO giveaways VALUES (?, '[]', '[]', ?, ?, ?)",
                             (self.name, 1 if self.isOpen else 0,
                              1 if self.followersOnly else 0, 1
                              if self.subscribersOnly else 0))
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
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            cur = await db.execute("INSERT INTO songs VALUES (?, ?, ?, 0)", (self.requester, self.song, self.requestedAt.strftime("%d/%m/%Y %H:%M:%S"),))
            self.rowID = cur.lastrowid
            await db.commit()

    async def play(self):
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
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
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            print(self.options)
            cur = await db.execute("INSERT INTO polls VALUES (?, '[]', 1)", (json.dumps(self.options),))
            await db.commit()
            self.rowid = cur.lastrowid

    @routines.routine(seconds=30)
    async def updateDB(self):
        await self.saveVotes()

    @updateDB.after_routine
    async def finalSave(self):
        await self.saveVotes()

    async def open(self):
        self.isOpen = True
        self.updateDB.start()

    async def close(self):
        self.isOpen = False
        self.updateDB.stop()

    async def saveVotes(self):
        async with aiosqlite.connect(f"data/user_{self.channelName}.db") as db:
            await db.execute("UPDATE polls SET options=?, voters=?, isOpen=? WHERE ROWID=?",
                             (json.dumps(self.options), json.dumps(self.voters), 1 if self.isOpen else 0, self.rowid))
            await db.commit()


@dataclass
class Quote:
    submittedAt: datetime
    submitter: str
    quote: str

    async def addToDB(self, channelName: str) -> Optional[int]:
        quoteCount = None
        async with aiosqlite.connect(f"data/user_{channelName}.db") as db:
            exists = await db.execute("SELECT 1 FROM quotes WHERE submitter=? AND quote=?", (self.submitter, self.quote,))
            if not await exists.fetchone():
                await db.execute("INSERT INTO quotes VALUES (?, ?, ?)", (self.submittedAt.strftime("%d/%m/%Y %H:%M:%S"), self.submitter, self.quote,))
                cur = await db.execute("SELECT COUNT(*) FROM quotes")
                quoteCount = await cur.fetchone()
                quoteCount = quoteCount[0]
                await db.commit()
        return quoteCount


@dataclass
class SteamInfo:
    categories: str
    genres: str
    developers: str


@dataclass
class Game:
    name: str
    id: int = field(default=0)
    image: str = field(default="")
    steamInfo: SteamInfo = field(default=None)


class Channel:
    def __init__(self, name: str, id: int, webhookID: int, webhookToken: str, isLive: int, title: str = "", whatgame: str = "", lastOnline: datetime = None):
        self.name: str = name
        self.displayName: str = self.name
        self.id: int = id

        self.webhookID: int = webhookID
        self.webhookToken: str = webhookToken
        self.thumbnailURL: str = ""

        self.isLive: bool = isLive == 1
        self.title: str = title
        self.game: Optional[Game] = None
        self.whatgame: str = whatgame
        self.lastOnline: datetime = lastOnline

        self.poll: Optional[Poll] = None
        self.songs: list = []
        self.requestsOpen: bool = True
        self.messages: list = []
        self.giveaways: dict = {}
        self.chatLogs: list = []

        self.channelObj: Optional[twitchio.Channel] = None

        self.giftsubs: dict = {}

        self.setupTables()
        self.loadFromDB()
        self.saveChatLogs.start()

    def __str__(self):
        return self.name

    def setupTables(self):
        Path("data").mkdir(exist_ok=True)
        con = sqlite3.connect(f"data/user_{self.name}.db")
        con.execute(f"CREATE TABLE IF NOT EXISTS chatlogs (date text, user text COLLATE NOCASE, message text COLLATE NOCASE)")
        #con.execute("DROP TABLE giveaways")
        con.execute("CREATE TABLE IF NOT EXISTS giveaways (keyword text unique primary key, entrants text, winners text, isOpen integer, "
                    "followersOnly integer, subscribersOnly integer)")
        con.execute("CREATE TABLE IF NOT EXISTS polls (options text, voters text, isOpen integer)")
        con.execute("CREATE TABLE IF NOT EXISTS quotes (submittedAt text, submitter text collate NOCASE, quote text collate NOCASE)")
        con.execute("CREATE TABLE IF NOT EXISTS whatgames (game text collate NOCASE, title text collate NOCASE, whatgame text collate NOCASE, dateAdded text)")
        con.execute("CREATE TABLE IF NOT EXISTS songs (requester text collate NOCASE, song text collate NOCASE, submittedAt text, played integer)")
        con.commit()
        con.close()

    def loadFromDB(self):
        con = sqlite3.connect(f"data/user_{self.name}.db")
        data = con.execute("SELECT * FROM giveaways WHERE isOpen=1").fetchall()
        self.giveaways = {giveaway[0]: Giveaway(channelName=self.name, name=giveaway[0], entrants=giveaway[1],
                                                winners=giveaway[2],
                                                followersOnly=giveaway[4] == 1, subscribersOnly=giveaway[5] == 1)
                          for giveaway in data}

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

        con = sqlite3.connect("data/generalTwitchInfo.db")
        webhookID, webhookToken, title, game, isLive, lastLive = con.execute("SELECT webhookID, webhookToken, title, game, liveStatus, lastOnline FROM channelInfo WHERE name=?",
                                                                     (self.name,)).fetchone()
        self.webhookID = webhookID
        self.webhookToken = webhookToken
        self.title = title
        self.game = Game(name=game)
        self.isLive = isLive == 1
        if lastLive is not None:
            self.lastOnline = datetime.strptime(lastLive, "%d/%m/%Y %H:%M:%S")
        else:
            self.lastOnline = None
        con.close()

    @routines.routine(minutes=1)
    async def saveChatLogs(self):
        if len(self.chatLogs) > 0:
            async with aiosqlite.connect(f"data/user_{self.name}.db") as db:
                await db.executemany(f"INSERT INTO chatlogs VALUES (?, ?, ?)", self.chatLogs)
                await db.commit()
            self.chatLogs = []

    async def openGiveaway(self, keyword: str, followersOnly: bool, subscribersOnly: bool) -> Giveaway:
        keyword = keyword.lower()
        giveaway = Giveaway(name=keyword, channelName=self.name, followersOnly=followersOnly,
                            subscribersOnly=subscribersOnly)
        self.giveaways[keyword] = giveaway
        await giveaway.addToDB(self.name)

        return giveaway

    async def addQuote(self, submittedAt: datetime, submitter: str, text: str) -> int:
        quote = Quote(submittedAt, submitter, text)
        quoteCount = None
        if self.name in ["akiss4luck", "essentia_modica", "scotbotm8", "quill18"]:
            names = ["akiss4luck", "essentia_modica", "scotbotm8", "quill18"]
        else:
            names = [self.name]

        for name in names:
            quoteCount = await quote.addToDB(name)

        return quoteCount

    async def getQuote(self, searchTerm: Optional[str], quoteNum: Optional[int]) -> Optional[tuple[Quote, int, int]]:
        async with aiosqlite.connect(f"data/user_{self.name}.db") as db:
            if searchTerm is None:
                cur = await db.execute("SELECT submittedAt, submitter, quote FROM quotes")
                quotes = await cur.fetchall()
            else:
                cur = await db.execute("SELECT submittedAt, submitter, quote FROM quotes WHERE submitter=? OR quote LIKE ?",
                                       (searchTerm, "%" + searchTerm + "%"))
                quotes = await cur.fetchall()

        quotes = [Quote(datetime.strptime(quote[0], "%d/%m/%Y %H:%M:%S") if quote[0] != "unknown" else datetime(year=1, month=1, day=1), quote[1], quote[2]) for quote in quotes]
        if len(quotes) == 0:
            return None
        if quoteNum is None:
            quoteNum = random.randrange(0, len(quotes))
        else:
            quoteNum -= 1
        quote = quotes[quoteNum]

        return quote, quoteNum + 1, len(quotes)

    async def addWhatgame(self, game: str, title: str, whatgame: str) -> bool:
        self.whatgame = whatgame
        async with aiosqlite.connect(f"data/user_{self.name}.db") as db:
            dateAdded = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            exists = await db.execute("SELECT 1 FROM whatgames WHERE game=? AND title=? AND whatgame=? AND dateAdded=?", (game, title, whatgame, dateAdded,))
            if not await exists.fetchone():
                await db.execute("INSERT INTO whatgames VALUES (?, ?, ?, ?)", (game, title, whatgame, dateAdded,))
                await db.commit()
                return True
            else:
                return False

    async def startPoll(self, options: list):
        self.poll = Poll({x: 0 for x in options}, self.name)
        await self.poll.open()

    async def closePoll(self):
        await self.poll.close()
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

    async def updateStreamInfo(self, game: bool = False, title: bool = False, isLive: bool = False, lastOnline: bool = False):
        async with aiosqlite.connect(f"data/generalTwitchInfo.db") as db:
            if game:
                await db.execute("UPDATE channelInfo SET game=? WHERE name=?", (self.game.name, self.name,))
            if title:
                await db.execute("UPDATE channelInfo SET title=? WHERE name=?", (self.title, self.name,))
            if isLive:
                await db.execute("UPDATE channelInfo SET liveStatus=? WHERE name=?", (1 if self.isLive else 0, self.name,))
            if lastOnline:
                await db.execute("UPDATE channelInfo SET lastOnline=? WHERE name=?", (datetime.strftime(self.lastOnline, "%d/%m/%Y %H:%M:%S"), self.name,))
            await db.commit()

    async def sendWebhook(self, changedGames: bool):
        if self.webhookID is None or self.webhookToken is None:
            return
        if not changedGames:
            header = f"{self.displayName} has gone live!"
        else:
            header = f"{self.displayName} has changed games"

        webhook = Webhook.partial(self.webhookID, self.webhookToken, adapter=RequestsWebhookAdapter())
        embed = Embed(title=header, description=f"https://www.twitch.tv/{self.displayName}", colour=Colour.purple())
        embed.add_field(name="Stream Title:", value=self.title, inline=False)
        embed.add_field(name="Now Playing:", value=self.game.name, inline=False)
        embed.set_image(url=self.game.image)
        embed.set_footer(icon_url=botImage, text="Scotbot - Created by DeadM8 for the QEB Community")
        embed.set_thumbnail(url=self.thumbnailURL)
        if changedGames:
            title = f"{self.displayName} has changed games..."
        elif self.name == "quill18":
            title = f"<@&651408409652101120>, Quill18 has gone live!"
        elif self.name in ["deadm8", "akiss4luck"]:
            title = f"@everyone, {self.displayName} has gone live!"
        else:
            title = f"{self.displayName} has gone live!"
        webhook.send(content=title, embed=embed)

    async def sendVOD(self, VOD: models.Video):
        if self.webhookID is None or self.webhookToken is None:
            return

        webhook = Webhook.partial(self.webhookID, self.webhookToken, adapter=RequestsWebhookAdapter())
        embed = Embed(title="Stream VOD", description=VOD.url, colour=Colour.purple())
        embed.add_field(name="VOD Title:", value=VOD.title)
        embed.set_thumbnail(url=self.thumbnailURL)
        webhook.send(content="The stream has ended. Check out the most recent VOD of the stream!", embed=embed)
