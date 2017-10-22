import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class ModerationAction:
    def __init__(self, name, reason, member):
        self.name = name
        self.reason = reason
        self.member = member


class Moderation:
    """Moderation related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.modlog_channel = None
        self.rustacean_role = None

    async def __error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('❌')

        if isinstance(error, discord.Forbidden):
            await ctx.send(f'The bot does not have permissions to do that! {error}')
        if isinstance(error, discord.HTTPException):
            await ctx.send(f'It failed! {error}')

    async def __before_invoke(self, ctx: commands.Context):
        if self.modlog_channel:
            return

        self.modlog_channel = self.bot.get_channel(id=274214329073795074)

        if not self.modlog_channel:
            raise RuntimeError('Failed to get modlog channel!')

    async def __after_invoke(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')

        action = ctx.action
        msg = await self.make_modlog_entry(ctx, action)
        await self.modlog_channel.send(msg)

    async def __local_check(self, ctx: commands.Context):
        return any(role.name in ('Admin', 'Moderator', 'Bot Admin') for role in ctx.author.roles)

    @commands.command()
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Kicks a member from the server.

        In order for this to work, the bot must have Kick Member permissions.

        To use this command you must have Kick Members permission or have the
        Bot Admin role.
        """

        ctx.action = ModerationAction(
            name='Kick',
            reason=reason,
            member=member,
        )

        await member.kick(reason=reason)

    @commands.command()
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Bans a member from the server.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission or have the
        Bot Admin role.
        """

        ctx.action = ModerationAction(
            name='Ban',
            reason=reason,
            member=member,
        )

        await member.ban(reason=reason, delete_message_days=0)

    @commands.command()
    @commands.guild_only()
    async def softban(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        To use this command you must have Ban Members permissions or have
        the Bot Admin role. Note that the bot must have the permission as well.
        """

        ctx.action = ModerationAction(
            name='Softban',
            reason=reason,
            member=member,
        )

        await member.ban(reason=reason, delete_message_days=0)
        await member.unban(reason=reason)

    @commands.command()
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Warns a member."""

        ctx.action = ModerationAction(
            name='Warn',
            reason=reason,
            member=member,
        )

    @commands.command()
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, limit=100):
        """Deletes up to 100 messages in the current channel."""

        deleted = await ctx.channel.purge(limit=limit)
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

    @commands.command()
    @commands.guild_only()
    async def rust(self, ctx: commands.Context, member: discord.Member):
        """Adds the Rustacean role to a member."""
        if not self.rustacean_role:
            self.rustacean_role = discord.utils.get(ctx.guild.roles, id=319953207193501696)
        await member.add_roles(self.rustacean_role)


    async def make_modlog_entry(self, ctx: commands.Context, action: ModerationAction):
        async for m in self.modlog_channel.history(limit=1):
            action_id = int(next(iter(m.content.split()))) + 1
    
        msg = '\n\n'.join([
            f'{action_id} | **{action.name}**',
            f'**User**\n{action.member.mention} ({str(action.member)} {action.member.id})',
            f'**Reason**\n{action.reason}',
            f'**Responsible Moderator**\n{ctx.message.author.mention}',
            f'**Timestamp**\n{ctx.message.created_at}',
        ])

        return msg


def setup(bot):
    bot.add_cog(Moderation(bot))
