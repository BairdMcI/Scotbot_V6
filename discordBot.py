import asyncio
import os
import pathlib
import random
import sqlite3
from abc import ABC
from time import strftime

import discord
import logging

from discord.ext import commands

import logger as _logger
from auth import discordToken
from discordClasses import ServerClass, presenceList, quillRoleAssignment, mainChannels

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
_logger.setupLogger(LOGGER)
LOGGER.propagate = False

os.chdir(os.path.join("/home", "ScotbotV6"))

intents = discord.Intents.all()
intents.members = True


class Scotbot(commands.Bot, ABC):
    def __init__(self):
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents,)
        self.SERVERS = {}
        cogs = [f"{p.parent}.{p.stem}" for p in pathlib.Path("discord_cogs").glob("*.py")]
        for extension in cogs:
            self.load_extension(extension)

        self.logger = LOGGER

    async def updatePresence(self):
        while True:
            await self.change_presence(activity=discord.Game(name=presenceList[random.randrange(len(presenceList))]))
            await asyncio.sleep(43200)

    async def checkIfMod(self, ctx: commands.Context):
        server: ServerClass = self.SERVERS[ctx.guild.name]
        if server.modRole is not None:
            if not any(role.id == server.modRole for role in ctx.author.roles):
                await ctx.send(f"{ctx.author.mention}, you don't have permission to use that command!")
                return False
        return True

    async def on_ready(self):
        self.SERVERS = {guild.name: ServerClass(guild.name, guild.id) for guild in self.guilds}
        self.SERVERS["Direct Messages"] = ServerClass("Direct Messages", None)

        LOGGER.info(f"Logged in as {self.user.name}")
        LOGGER.info(f"Connecting to channels... {', '.join([server.name for server in self.SERVERS.values()])}")

        for server in self.SERVERS.values():
            server: ServerClass
            await server.initialLoad()
            await server.fetchModRole()
            await server.fetchGiveaways()
            if len(server.giveaways) > 0:
                channelNames = [self.get_channel(channelID).name for channelID in [*server.giveaways]]
                LOGGER.info(f"{server.name} has giveaways open in the following channels: {'; '.join(channelNames)}")
            self.loop.create_task(server.saveChatLogs())

        self.loop.create_task(self.updatePresence())

    async def on_message(self, message: discord.Message):
        output = f"{strftime('%d/%m/%Y %H:%M:%S')} | {message.author.name}: {message.clean_content}"
        if message.author.display_name == "ScotBot":
            logLevel = 7
        else:
            logLevel = 5
        if message.guild is None:
            server: ServerClass = self.SERVERS["Direct Messages"]

            if message.channel.recipient not in server.chats.keys():
                server.chats[message.channel.recipient] = [output]
            else:
                server.chats[message.channel.recipient].append(output)
        else:
            server: ServerClass = self.SERVERS[message.guild.name]
            if message.guild.name not in server.chats.keys():
                server.chats[message.guild.name] = [output]
            else:
                server.chats[message.guild.name].append(output)

        LOGGER.log(logLevel, f"{f'{message.guild.name} | {message.channel.name}' if message.guild is not None else 'Direct Message'} | {output}")
        await self.process_commands(message)

    async def on_member_join(self, member: discord.Member):
        generalChannel = [channel for channel in member.guild.channels if channel.name == "general"]
        server: discord.abc.GuildChannel = member.guild.get_channel(mainChannels[member.guild.name])
        await generalChannel[0].send(f"Welcome to the {member.guild.name} discord server, {member.mention}! Please make sure to check {server.mention}, and enjoy your stay!")

    async def on_member_update(self, before, after):
        before: discord.Member
        if before.guild.name == "Quill18":
            if "Twitch Subscriber" in [role.name for role in before.roles] and "Twitch Subscriber" not in [role.name for role in after.roles]:
                await before.send("Hey there! It appears your Twitch sub to Quill18 has lapsed! If you'd like to continue to support Quill, and retain the perks that subscribing gives you, including "
                                  "access to the sub-only Discord, then make sure to renew your subscription at http://www.twitch.tv/quill18. Thanks! NOTE: This is an automated message. Please contact DeadM8 for queries")
                LOGGER.info(f"Sub lapse notification sent to {before.name}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id == 651856904993112084:
            guild: discord.Guild = self.get_guild(payload.guild_id)
            user: discord.Member = guild.get_member(payload.user_id)
            newRole: discord.Role = guild.get_role(quillRoleAssignment[payload.emoji.name])
            if not any(role.id == newRole.id for role in user.roles):
                await user.add_roles(newRole)
                try:
                    await user.send(f"Hey there! You've been added to the {newRole.name} role in the {guild.name} Discord server")
                except discord.Forbidden:
                    LOGGER.info(f"{guild.name} | Unable to send DM to {user.name} - Direct Messages disabled")
                LOGGER.info(f"{guild.name} | {user.name} added to {newRole.name} role")

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id == 651856904993112084:
            guild: discord.Guild = self.get_guild(payload.guild_id)
            user: discord.Member = guild.get_member(payload.user_id)
            newRole: discord.Role = guild.get_role(quillRoleAssignment[payload.emoji.name])
            if any(role.id == newRole.id for role in user.roles):
                await user.remove_roles(newRole)
                await user.send(f"Hey there! You've been removed from the {newRole.name} role in the {guild.name} Discord server")
                LOGGER.info(f"{guild.name} | {user.name} removed from {newRole.name} role")


if __name__ == "__main__":
    BOT = Scotbot()
    BOT.run(discordToken)
