import asyncio
import logging

import discord
from discord.ext import commands
from discord.utils import find

log = logging.getLogger('rust_bot')


class Join:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        server = self.bot.get_server(id='273534239310479360')
        self.rustacean_role = find(lambda m: m.id == '273539307254448128', server.roles)
        self.welcome_channel = self.bot.get_channel(id='273539505561010187')
        self.join_channel = self.bot.get_channel(id='278360426213933056')

    async def on_member_join(self, member: discord.Member):
        msg = await self.bot.send_message(self.welcome_channel,
                                          f'Welcome to the **Rust Programming Language** server, {member.mention}!\n'
                                          'Please take a minute to read the <#273534239310479360>.\n'
                                          'You\'ll get permission to speak shortly.')

        await asyncio.sleep(60)

        await self.bot.delete_message(msg)

        try:
            await self.bot.add_roles(member, self.rustacean_role)
        except (discord.Forbidden, discord.HTTPException) as e:
            log.exception(f'on_member_join exception: {e}')


def setup(bot):
    bot.add_cog(Join(bot))
