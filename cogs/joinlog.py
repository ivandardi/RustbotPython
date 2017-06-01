import logging
from datetime import datetime

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class JoinLog:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.modjoin_channel_id = 278360426213933056

    def modjoin_channel(self, guild: discord.Guild):
        return guild.get_channel(channel_id=self.modjoin_channel_id)

    async def on_member_join(self, member: discord.Member):

        embed = discord.Embed(title=f'{member.name}', color=discord.Color.green())
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Created at', value=member.created_at)
        embed.timestamp = datetime.utcnow()

        await self.send_message(member.guild, embed)

    async def on_member_remove(self, member: discord.Member):

        embed = discord.Embed(title=f'{member.name}', color=discord.Color.red())
        embed.add_field(name='ID', value=member.id)
        embed.timestamp = datetime.utcnow()

        await self.send_message(member.guild, embed)

    async def send_message(self, guild: discord.Guild, embed: discord.Embed):
        try:
            await self.modjoin_channel(guild).send(embed=embed)
        except discord.Forbidden as e:
            log.exception('No permissions to send message!')
            log.exception('Exception: {}'.format(e))
        except discord.NotFound as e:
            log.exception('The mod-log channel was not found!')
            log.exception('Exception: {}'.format(e))
        except discord.HTTPException as e:
            log.exception('Sending the message failed!')
            log.exception('Exception: {}'.format(e))
        except discord.InvalidArgument as e:
            log.exception('The destination parameter is invalid')
            log.exception('Exception: {}'.format(e))


def setup(bot):
    bot.add_cog(JoinLog(bot))
