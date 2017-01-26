import datetime
import logging
import traceback

import discord
from discord.ext import commands

import utils

description = """
Hello! I am a bot written by MelodicStream#1336 to manage the Rust server!
"""

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

log = utils.setup_logger('rust_bot')

help_attrs = dict(hidden=True)

bot = commands.Bot(command_prefix=['!', '?'], description=description, pm_help=True, help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        log.error('Command error')
        log.error('In {0.command.qualified_name}:'.format(ctx))
        traceback.print_tb(error.original.__traceback__)
        log.error('{0.__class__.__name__}: {0}'.format(error.original))


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    print('DON\'T FORGET TO RUN ?reload')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()

    await bot.change_presence(game=discord.Game(name='?help'))


@bot.event
async def on_command(command, ctx):
    message = ctx.message
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name}'.format(message)

    log.info('{0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)


if __name__ == '__main__':
    token = utils.load_credentials()['token']

    bot.load_extension('cogs.admin')

    bot.run(token)

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
