import sqlite3

from twitchClasses import Channel


def getChannelInfo(con: sqlite3.Connection, channelName: str) -> Channel:
    channelInfo = con.execute(f"SELECT name, id, webhookId, webhookToken, liveStatus FROM channelInfo WHERE name=?", (channelName,)).fetchone()
    data = Channel(name=channelInfo[0], id=channelInfo[1], webhookID=channelInfo[2], webhookToken=channelInfo[3], isLive=channelInfo[4])
    return data


def getAllChannelNames(con: sqlite3.Connection) -> list:
    data = con.execute(f"SELECT name FROM channelInfo").fetchall()
    data = [x[0] for x in data]
    return data


def getAllChannelInfo(con: sqlite3.Connection) -> list:
    data = [getChannelInfo(con, channel) for channel in getAllChannelNames(con)]
    return data
