import datetime
import logging
import os

import discord
from discord.ext import commands


def setup_logger():
    handler = logging.FileHandler(filename='logging.log', encoding='utf-8', mode='w')

    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(module)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
log = setup_logger()


class SelfBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uptime = None

        self.initial_extensions = [
            'cogs.admin',
            'cogs.joinlog',
            'cogs.meta',
            'cogs.mod',
            'cogs.playground',
        ]

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        if not self.uptime:
            self.uptime = datetime.datetime.utcnow()

    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination = 'Private Message'
        else:
            destination = f'#{ctx.channel.name} ({ctx.guild.name})'

        log.info(f'{destination}: {ctx.message.content}')


if __name__ == '__main__':

    bot = SelfBot(
        command_prefix=['!', '?'],
    )

    for extension in bot.initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:  # noqa
            print(f'Failed to load extension {extension}\n{type(e).__name__}: {e}')

    bot.run(os.environ['TOKEN'])

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
