import contextlib
import json
import logging
import os

from discord.ext import commands

from bot import RustBot


@contextlib.contextmanager
def setup_logging():
    logger = logging.getLogger("bot")

    logger.setLevel(logging.INFO)

    try:
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

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        yield
    finally:
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)


def main():
    with open(os.environ["CONFIG_FILE"]) as f:
        config = json.load(f)

    with setup_logging():
        bot = RustBot(
            command_prefix=commands.when_mentioned_or(*config["prefixes"]),
            config=config,
        )
        bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == '__main__':
    main()
