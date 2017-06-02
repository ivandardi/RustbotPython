import json
import logging

import aiohttp
from discord.ext import commands

log = logging.getLogger(__name__)


async def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```rs\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')


class Playground:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client_session = aiohttp.ClientSession(loop=self.bot.loop)

    @commands.command()
    async def play(self, ctx: commands.Context, *, code: str = None):
        """Exactly equal to http://play.integer32.com/"""

        if not code:
            return await ctx.message.add_reaction('❌')

        code = await cleanup_code(code)

        payload = json.dumps({
            'channel': 'nightly',
            'code': code,
            'crateType': 'bin',
            'mode': 'debug',
            'tests': False,
        })

        async with self.client_session.post('http://play.integer32.com/execute', data=payload) as r:
            response = await r.json()

            if 'error' in response:
                log.error(f'Playground error: {response["error"]}')
                await ctx.message.add_reaction('❌')
                return

            msg = f"```rs\n{response['stderr']}\n{response['stdout']}\n```"

            await ctx.message.add_reaction('👌')
            await ctx.send(msg)


def setup(bot):
    bot.add_cog(Playground(bot))
