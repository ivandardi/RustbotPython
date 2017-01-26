import inspect

import discord
from discord.ext import commands

from utils import checks, initial_extensions


class Admin:
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_owner()
    async def close(self):
        """Closes the bot safely."""
        await self.bot.logout()

    @commands.command(hidden=True)
    @checks.is_owner()
    async def status(self, *, status: str):
        """Changes the bot's status."""
        await self.bot.change_presence(game=discord.Game(name=status))

    @commands.command(hidden=True)
    @checks.is_owner()
    async def load(self, *, module: str):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(hidden=True)
    @checks.is_owner()
    async def unload(self, *, module: str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(name='reload', hidden=True)
    @checks.is_owner()
    async def _reload(self, *, module: str = None):
        """Reloads a module."""
        try:
            if module:
                self.bot.unload_extension(module)
                self.bot.load_extension(module)
            else:
                for m in initial_extensions:
                    self.bot.unload_extension(m)
                    self.bot.load_extension(m)
        except Exception as e:
            await self.bot.say('Failed to reload extensions!\n{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""
        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'msg': ctx.message,
            'srv': ctx.message.server,
            'cnl': ctx.message.channel,
            'ath': ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await self.bot.say(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await self.bot.say(python.format(result))


def setup(bot):
    bot.add_cog(Admin(bot))
