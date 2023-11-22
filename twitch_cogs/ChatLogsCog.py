from twitchio.ext import commands, routines
from twitchBot import Scotbot
from twitchClasses import Channel


class ChatLogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot: Scotbot = bot

    @routines.routine(minutes=1)
    async def saveChatLogs(self):
        for channel in self.bot.channels.values():
            print(channel.chatLogs)
            if len(channel.chatLogs) > 0:
                async with aiosqlite.connect(f"data/user_{channel.name}.db") as db:
                    await db.executemany(f"INSERT INTO chatlogs VALUES (?, ?, ?)", channel.chatLogs)
                    await db.commit()
                self.bot.logger.info(f"Saved {len(channel.chatLogs)} messages in {channel.name}")
                channel.chatLogs = []


def prepare(bot):
    bot.add_cog(ChatLogsCog(bot))
