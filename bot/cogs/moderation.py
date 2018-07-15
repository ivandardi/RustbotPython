import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(
                    f"{argument} is not a valid member or member ID."
                ) from None
        else:
            can_execute = (
                ctx.author.id == ctx.bot.owner_id
                or ctx.author == ctx.guild.owner
                or ctx.author.top_role > m.top_role
            )

            if not can_execute:
                raise commands.BadArgument(
                    "You cannot do this action on this user due to role hierarchy."
                )
        return m.id


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")

        return entity


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

    async def __error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction("❌")

        if isinstance(error, discord.Forbidden):
            await ctx.send(f"The bot does not have permissions to do that! {error}")
        if isinstance(error, discord.HTTPException):
            await ctx.send(f"It failed! {error}")

    async def __before_invoke(self, ctx: commands.Context):
        if self.modlog_channel:
            return

        self.modlog_channel = self.bot.get_channel(id=274214329073795074)

        if not self.modlog_channel:
            raise RuntimeError("Failed to get modlog channel!")

    async def __after_invoke(self, ctx: commands.Context):
        await ctx.message.add_reaction("👌")

        try:
            action = ctx.action
            msg = await self.make_modlog_entry(ctx, action)
            await self.modlog_channel.send(msg)
        except AttributeError:
            pass

    async def __local_check(self, ctx: commands.Context):
        return any(
            role.name in ("Admin", "Moderator", "Bot Admin")
            for role in ctx.author.roles
        )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: MemberID, *, reason: str):
        """Kicks a member from the server.

        In order for this to work, the bot must have Kick Member permissions.

        To use this command you must have Kick Members permission or have the
        Bot Admin role.
        """

        ctx.action = ModerationAction(name="Kick", reason=reason, member=member)

        await ctx.guild.kick(discord.Object(id=member), reason=reason)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self, ctx: commands.Context, member: MemberID, days: int, *, reason: str
    ):
        """Bans a member from the server.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission or have the
        Bot Admin role.
        """

        ctx.action = ModerationAction(name="Ban", reason=reason, member=member)

        await ctx.guild.ban(
            discord.Object(id=member), reason=reason, delete_message_days=days
        )

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def softban(
        self, ctx: commands.Context, member: MemberID, days: int, *, reason: str
    ):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        To use this command you must have Ban Members permissions or have
        the Bot Admin role. Note that the bot must have the permission as well.
        """

        ctx.action = ModerationAction(name="Softban", reason=reason, member=member)

        obj = discord.Object(id=member)
        await ctx.guild.ban(obj, reason=reason, delete_message_days=days)
        await ctx.guild.unban(obj, reason=reason)
        await member.unban(reason=reason)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: BannedMember, *, reason: str):
        """Unbans a member from the server.

        You can pass either the ID of the banned member or the Name#Discrim
        combination of the member. Typically the ID is easiest to use.

        To use this command you must have Ban Members permissions or have
        the Bot Admin role. Note that the bot must have the permission as well.
        """

        previous_reason = ""
        if member.reason:
            previous_reason = f'\nUser was previously banned for "{member.reason}".'

        ctx.action = ModerationAction(
            name="Unban", reason=f"{reason}{previous_reason}", member=member.user
        )

        await ctx.guild.unban(member.user, reason=reason)

    @commands.command()
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Warns a member."""

        ctx.action = ModerationAction(name="Warn", reason=reason, member=member)

    @commands.command()
    @commands.guild_only()
    async def purge(self, ctx: commands.Context, limit=100):
        """Deletes up to 100 messages in the current channel."""

        deleted = await ctx.channel.purge(limit=limit)
        await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)

    async def make_modlog_entry(self, ctx: commands.Context, action: ModerationAction):
        async for m in self.modlog_channel.history(limit=1):
            action_id = int(next(iter(m.content.split()))) + 1

        msg = "\n\n".join(
            [
                f"{action_id} | **{action.name}**",
                f"**User**\n{action.member.mention} ({str(action.member)} {action.member.id})",
                f"**Reason**\n{action.reason}",
                f"**Responsible Moderator**\n{ctx.author.mention} (ID: {ctx.author.id})",
                f"**Timestamp**\n{ctx.message.created_at}",
            ]
        )

        return msg


def setup(bot):
    bot.add_cog(Moderation(bot))
