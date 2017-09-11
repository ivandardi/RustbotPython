import asyncio
import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class JoinLog:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = None
        self.ferris_emoji = None
        self.newcomer_role = None

    async def initialize(self, guild: discord.Guild):
        await self.bot.wait_until_ready()

        if not self.welcome_channel:
            self.welcome_channel = self.bot.get_channel(id=338125445256052736)
        if not self.ferris_emoji:
            self.ferris_emoji = self.bot.get_emoji(id=298953944292392960)
        if not self.newcomer_role:
            self.newcomer_role = discord.utils.get(guild.roles, id=356627450790281216)

        if not all([self.welcome_channel, self.ferris_emoji, self.newcomer_role]):
            raise RuntimeError('Failed to initialize joinlog!')

    async def on_member_join(self, member: discord.Member):
        await self.initialize(member.guild)

        if member.bot:
            return

        await member.add_roles(self.newcomer_role, reason='Newcomer to the server')
        await self.welcome_channel.send(
            f'[{member} ({member.id})]\n'
            f'{member.mention}, welcome to the **Rust Programming Language** server!'
        )
        msg = await self.welcome_channel.send(
            f"{member.mention}, If you're here for the language, react with the Ferris.\n"
            "If you're here for Rust the game, react with the game controller.\n\n"
            "If you're here for the game, reacting with the game controller will kick you "
            "from this server so that you can look for the right Rust server.\n"
            "If you take more than 5 minutes to react, **you'll be kicked**."
        )
        await msg.add_reaction('\N{VIDEO GAME}')
        await msg.add_reaction(self.ferris_emoji)

        def react_check(reaction, user):
            if not user or user.id != member.id:
                return False

            if reaction.message.id != msg.id:
                return False

            if reaction.emoji in (self.ferris_emoji, '\N{VIDEO GAME}'):
                return True

            return False

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=react_check, timeout=60 * 5)
        except asyncio.TimeoutError:
            await member.kick(reason="Didn't react to welcome message in time")
        else:
            emoji = reaction.emoji
            if isinstance(emoji, str) and emoji == '\N{VIDEO GAME}':
                return await member.kick(reason='Wrong Rust server')
        finally:
            await msg.delete()
            await member.remove_roles(self.newcomer_role, reason='Passed the welcome check')

    async def on_member_remove(self, member: discord.Member):
        await self.initialize(member.guild)
        await self.welcome_channel.send(f'[{member} ({member.id})]\n'
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
