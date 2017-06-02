import logging

import discord
from discord.ext import commands

from .utils import checks

log = logging.getLogger(__name__)


class ModerationAction:
    def __init__(self, name, reason, member):
        self.name = name
        self.reason = reason
        self.member = member


class Mod:
    """Moderation related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.modlog_channel_id = 274214329073795074

    def modlog_channel(self, ctx: commands.Context):
        return ctx.guild.get_channel(self.modlog_channel_id)

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
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

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
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

        await member.ban(reason=reason)

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
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

        await member.ban(reason=reason)
        await member.unban(reason=reason)

    @ban.error
    @kick.error
    @softban.error
    async def mod_error(self, error, ctx: commands.Context):
        await ctx.message.add_reaction('❌')

        action = ctx.action
        if isinstance(error, discord.Forbidden):
            return await ctx.send(f'The bot does not have permissions to {action.name} members.')
        if isinstance(error, discord.HTTPException):
            return await ctx.send(f'{action.name} failed.')

    @ban.after_invoke
    @kick.after_invoke
    @softban.after_invoke
    async def add_to_modlog(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')

        action = ctx.action
        msg = await self.make_modlog_entry(ctx, action)
        await self.modlog_channel(ctx).send(msg)

    async def make_modlog_entry(self, ctx: commands.Context, action: ModerationAction):

        async for m in self.modlog_channel(ctx).history(limit=1):
            action_id = int(next(iter(m.content.split()))) + 1

        msg = '\n\n'.join([
            f'{action_id} | **{action.name}**',
            f'**User**\n{action.member.mention} ({str(action.member)} {action.member.id})',
            f'**Reason**\n{action.reason}',
            f'**Responsible Moderator**\n{ctx.message.author.mention}',
            f'**Timestamp**\n{ctx.message.created_at}',
        ])

        return msg

    @commands.command(no_pm=True, aliases=['prune', 'remove'])
    @checks.admin_or_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit=100):
        """Deletes up to 100 messages in the current channel."""

        deleted = await ctx.channel.purge(limit=limit)
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)


def setup(bot):
    bot.add_cog(Mod(bot))
