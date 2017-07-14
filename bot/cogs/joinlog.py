import logging
from datetime import datetime

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class JoinLog:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.modjoin_channel = self.bot.get_channel(id=278360426213933056)

    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title=f'{member.name}', color=discord.Color.green())
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Created at', value=member.created_at)
        embed.timestamp = datetime.utcnow()

        await self.modjoin_channel.send(embed=embed)

    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(title=f'{member.name}', color=discord.Color.red())
        embed.add_field(name='ID', value=member.id)
        embed.timestamp = datetime.utcnow()

        await self.modjoin_channel.send(embed=embed)

    async def __error(self, ctx: commands.Context, error):
        if isinstance(error, discord.Forbidden):
            log.exception('No permissions to send message!')
        if isinstance(error, discord.NotFound):
            log.exception('The mod-log channel was not found!')
        if isinstance(error, discord.HTTPException):
            log.exception('Sending the message failed!')
        if isinstance(error, discord.InvalidArgument):
            log.exception('The destination parameter is invalid')
        log.exception('JoinLog Exception: %s', error)


def setup(bot):
    bot.add_cog(JoinLog(bot))
