import json
import logging

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class CodeBlock:
    missing_error = 'Missing code block. Please use the following markdown\n\\`\\`\\`language\ncode here\n\\`\\`\\`'

    def __init__(self, argument):
        try:
            block, code = argument.split('\n', 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith('```') and not code.endswith('```'):
            raise commands.BadArgument(self.missing_error)

        self.source = code.rstrip('`')


class Playground:
    """Evaluates Rust code.

    Usage:

    ?play ```rs
    <your Rust code here>
    ```

    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    async def play(self, ctx: commands.Context, *, code: CodeBlock):
        """Evaluates Rust code. Exactly equal to http://play.integer32.com/"""

        payload = json.dumps({
            'channel': 'nightly',
            'code': code.source,
            'crateType': 'bin',
            'mode': 'debug',
            'tests': False,
        })

        async with self.session.post('http://play.integer32.com/execute', data=payload) as r:
            if r.status != 200:
                raise commands.CommandError("Rust i32 Playgrond didn't respond in time.")
            response = await r.json()

        if 'error' in response:
            error = response['error']
            log.error(f'Playground error: {error}')
            raise commands.CommandError(error)

        msg = f"```rs\n{response['stderr']}{response['stdout']}\n```"

        await ctx.send(msg)

    @play.error
    async def play_error(self, ctx: commands.Context, error):
        if isinstance(error, (discord.HTTPException, discord.Forbidden)):
            await ctx.send('Error while sending the output.')
        elif isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        await ctx.message.add_reaction('❌')

    @play.after_invoke
    async def play_after(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')


def setup(bot):
    bot.add_cog(Playground(bot))
