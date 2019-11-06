import datetime
import logging
import traceback

import discord
from discord.ext import commands

from bot.guild_caches import GuildEmojis, GuildRoles

log = logging.getLogger(__name__)


class RustBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uptime = datetime.datetime.utcnow()
        self.config = kwargs["config"]
        self.custom_extensions = self.config["extensions"]
        self.guild = None
        self.emoji = None
        self.role = None

        for extension in self.custom_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:  # noqa
                log.error("Failed to load extension %s\n%s: %s", extension, type(e).__name__, e)

    async def on_ready(self):
        log.info("Logged in as %s", self.user)

        await self.change_presence(activity=discord.Game(name="?help"))

        self.guild = await self.fetch_guild(self.config["guild_id"])

        self.emoji = GuildEmojis(self.config["emojis"], self.guild.emojis)
        self.role = GuildRoles(self.config["roles"], self.guild.roles)

    async def on_command(self, ctx):
        destination = f"#{ctx.channel}"
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination += f" ({ctx.guild})"
        log.info(f"{ctx.author} in {destination}: {ctx.message.content}")

    async def on_command_error(self, ctx: commands.Context, error):
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        log.error(f"Command error in %s:\n%s", ctx.command, tb)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.add_reaction("❌")
            await ctx.send(f"You aren't allowed to run this command!")

    async def on_member_join(self, member: discord.Member):
        if member.guild == self.guild:
            await member.add_roles(
                self.role.rustacean, reason=f"You have been automatically rusted! owo"
            )
