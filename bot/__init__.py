import datetime
import logging
import os
import traceback

import discord
from discord.ext import commands


def setup_logging():
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{"
    )

    file_handler = logging.FileHandler(
        filename="logging.log", encoding="utf-8", mode="w"
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


class RustBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uptime = datetime.datetime.utcnow()
        self.initial_extensions = [
            "bot.cogs.meta",
            "bot.cogs.owner",
            "bot.cogs.playground",
        ]
        self.rust_guild = None
        self.emoji_rustok = None
        self.rustacean_role = None
        self.log = setup_logging()

        for extension in self.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:  # noqa
                print(f"Failed to load extension {extension}\n{type(e).__name__}: {e}")

    async def on_ready(self):
        print("Logged in as", self.user)
        print("------")

        await self.change_presence(activity=discord.Game(name="?help"))

        self.emoji_rustok = discord.utils.get(self.emojis, name="rustOk")
        if self.emoji_rustok:
            self.log.info("Emoji rustOk loaded!")
        else:
            self.log.info("Emoji rustOk not loaded! D:")

        self.rust_guild = await self.fetch_guild(273534239310479360)
        if self.rust_guild:
            self.log.info("Fetched Rust guild, fetching Rustacean role...")
            self.rustacean_role = self.rust_guild.get_role(319_953_207_193_501_696)
            if self.rustacean_role:
                self.log.info("Rustacean role loaded!")
            else:
                self.log.info("Rustacean role not loaded! D:")
        else:
            self.log.info("Failed to fetch Rust guild")

    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination = f"#{ctx.channel}"
        else:
            destination = f"#{ctx.channel} ({ctx.guild})"
        self.log.info(f"{ctx.author} in {destination}: {ctx.message.content}")

    async def on_command_error(self, ctx: commands.Context, error):
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self.log.error(f"Command error in %s:\n%s", ctx.command, tb)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.add_reaction("❌")
            await ctx.send(f"You aren't allowed to run this command!")

    async def on_member_join(self, member: discord.Member):
        if member.guild == self.rust_guild:
            await member.add_roles(
                self.rustacean_role, reason=f"You have been automatically rusted! owo"
            )


def main():
    bot = RustBot(
        command_prefix=commands.when_mentioned_or(
            "?",
            "\N{CRAB} ",
            "\N{CRAB}",
            "hey ferris can you please ",
            "hey ferris, can you please ",
            "hey fewwis can you please ",
            "hey fewwis, can you please ",
            "hey ferris can you ",
            "hey ferris, can you ",
            "hey fewwis can you ",
            "hey fewwis, can you ",
        )
    )

    bot.run(os.environ["TOKEN_DISCORD"])

    handlers = bot.log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        bot.log.removeHandler(hdlr)
