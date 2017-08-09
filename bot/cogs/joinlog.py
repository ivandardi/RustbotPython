import asyncio
import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class JoinLog:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._welcome_channel = None
        self._ferris_emoji = None
        self.overwrites = discord.PermissionOverwrite(send_messages=False, read_messages=True)

    async def welcome_channel(self):
        if not self._welcome_channel:
            await self.bot.wait_until_ready()
            log.debug('Getting welcome channel')
            self._welcome_channel = self.bot.get_channel(id=338125445256052736)
            if not self._welcome_channel:
                raise RuntimeError('Failed to get welcome channel!')
        return self._welcome_channel

    async def ferris_emoji(self):
        if not self._ferris_emoji:
            await self.bot.wait_until_ready()
            self._ferris_emoji = self.bot.get_emoji(id=298953944292392960)
            if not self._ferris_emoji:
                raise RuntimeError('Failed to get ferris emoji!')
        return self._ferris_emoji

    async def on_member_join(self, member: discord.Member):
        welcome_channel = await self.welcome_channel()
        ferris_emoji = await self.ferris_emoji()

        if member.bot:
            return

        await self.set_global_permissions(member=member, overwrite=self.overwrites)

        await welcome_channel.send(f'[{member} ({member.id})]\n'
                                   f'{member.mention}, welcome to the **Rust Programming Language** server!')
        msg = await welcome_channel.send(f"{member.mention}, If you're here for the language, click on the Ferris.\n"
                                         "If you're here for Rust the game, click on the game controller.\n"
                                         "If you take more than 5 minutes to react, you'll be kicked.")
        await msg.add_reaction('\N{VIDEO GAME}')
        await msg.add_reaction(ferris_emoji)

        def react_check(reaction, user):
            if not user or user.id != member.id:
                return False

            if reaction.message.id != msg.id:
                return False

            if reaction.emoji in (ferris_emoji, '\N{VIDEO GAME}'):
                return True

            return False

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=react_check, timeout=300.0)
        except asyncio.TimeoutError:
            await member.kick(reason="Didn't react to welcome message in time")
        else:
            emoji = reaction.emoji
            if isinstance(emoji, str) and emoji == '\N{VIDEO GAME}':
                return await member.kick(reason='Wrong Rust server')
            await self.set_global_permissions(member=member, overwrite=None)
        finally:
            await msg.delete()

    async def set_global_permissions(self, *, member, overwrite):
        for channel in member.guild.channels:
            try:
                await channel.set_permissions(member, overwrite=overwrite)
            except Exception as e:
                log.error('set_global_permissions on %s: %s', channel, e)

    async def on_member_remove(self, member: discord.Member):
        welcome_channel = await self.welcome_channel()
        await welcome_channel.send(f'[{member} ({member.id})]\n'
                                   f'Goodbye, {member.mention} :(')

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
