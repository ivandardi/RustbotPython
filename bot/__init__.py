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


log = setup_logging()


class RustBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uptime = datetime.datetime.utcnow()
        self.initial_extensions = [
            "bot.cogs.meta",
            "bot.cogs.owner",
            "bot.cogs.playground",
        ]
        self.emoji_rustok = None
        self.log = log

        for extension in self.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:  # noqa
                print(f"Failed to load extension {extension}\n{type(e).__name__}: {e}")

    async def on_ready(self):
        print("Logged in as", self.user)
        print("------")

        await self.change_presence(activity=discord.Game(name="??help"))
        self.emoji_rustok = discord.utils.get(self.emojis, name="rustOk")
        if self.emoji_rustok:
            log.info("Emoji rustOk loaded!")
        else:
            log.info("Emoji rustOk not loaded! D:")

    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination = f"#{ctx.channel}"
        else:
            destination = f"#{ctx.channel} ({ctx.guild})"
        log.info(f"{ctx.author} in {destination}: {ctx.message.content}")

    async def on_command_error(self, ctx: commands.Context, error):
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        log.error(f"Command error in %s:\n%s", ctx.command, tb)
        if isinstance(error, commands.CheckFailure):
            await ctx.message.add_reaction("❌")
            await ctx.send(f"You aren't allowed to run this command!")


def main():
    bot = RustBot(
        command_prefix=commands.when_mentioned_or(
            "?",
            "🦀",
            "🦀 ",
            "hey ferris can you ",
            "hey ferris can you please ",
            "hey ferris, can you ",
            "hey ferris, can you please",
            "hey fewwis can you ",
            "hey fewwis can you please",
            "hey fewwis, can you ",
            "hey fewwis, can you please",
        )
    )

    bot.run(os.environ["TOKEN_DISCORD"])

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
