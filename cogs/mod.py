import logging
from collections import Counter

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import Context

from utils import checks

log = logging.getLogger('rust_bot')


class Mod:
    """Moderation related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.modlog_channel = self.modlog_channel = self.bot.get_channel(id='274214329073795074')

    async def embed_format(self, ctx: Context, member: discord.Member, reason: str, color: Color, action: str):

        async for m in self.bot.logs_from(channel=self.modlog_channel, limit=1):
            action_id = int(m.embeds[0]['title'].split()[0]) + 1

        embed = discord.Embed(title=f'{action_id} | **{action}**', color=color)
        embed.add_field(name='User', value=f'{member.mention} ({member.id})', inline=False)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Responsible Moderator', value=ctx.message.author.mention, inline=False)
        embed.timestamp = ctx.message.timestamp

        return embed

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
    async def kick(self, ctx: commands.context.Context, member: discord.Member, *, reason: str):
        """Kicks a member from the server.

        In order for this to work, the bot must have Kick Member permissions.

        To use this command you must have Kick Members permission or have the
        Bot Admin role.
        """

        try:
            await self.bot.kick(member)
        except discord.Forbidden:
            await self.bot.say('The bot does not have permissions to kick members.')
        except discord.HTTPException:
            await self.bot.say('Kicking failed.')
        else:
            await self.bot.say('\U0001f44c')
            await self.bot.send_message(self.modlog_channel,
                                        embed=await self.embed_format(ctx, member, reason, Color.gold(), 'Kick'))

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ban(self, ctx: commands.context.Context, member: discord.Member, *, reason: str):
        """Bans a member from the server.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission or have the
        Bot Admin role.
        """

        try:
            await self.bot.ban(member)
        except discord.Forbidden:
            await self.bot.say('The bot does not have permissions to ban members.')
        except discord.HTTPException:
            await self.bot.say('Banning failed.')
        else:
            await self.bot.say('\U0001f44c')
            await self.bot.send_message(self.modlog_channel,
                                        embed=await self.embed_format(ctx, member, reason, Color.red(), 'Ban'))

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def softban(self, ctx: commands.context.Context, member: discord.Member, *, reason: str):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        To use this command you must have Ban Members permissions or have
        the Bot Admin role. Note that the bot must have the permission as well.
        """

        try:
            await self.bot.ban(member)
            await self.bot.unban(member.server, member)
        except discord.Forbidden:
            await self.bot.say('The bot does not have permissions to ban members.')
        except discord.HTTPException:
            await self.bot.say('Banning failed.')
        else:
            await self.bot.say('\U0001f44c')
            await self.bot.send_message(self.modlog_channel,
                                        embed=await self.embed_format(ctx, member, reason, Color.orange(), 'Softban'))

    @commands.group(pass_context=True, no_pm=True, aliases=['remove', 'prune'])
    @checks.admin_or_permissions(manage_messages=True)
    async def purge(self, ctx: commands.context.Context):
        """Removes messages that meet a criteria.

        In order to use this command, you must have Manage Messages permissions
        or have the Bot Admin role. Note that the bot needs Manage Messages as
        well. These commands cannot be used in a private message.

        When the command is done doing its work, you will get a private message
        detailing which users got removed and how many messages got removed.
        """

        if ctx.invoked_subcommand is None:
            await self.bot.say('Invalid criteria passed "{0.subcommand_passed}"'.format(ctx))

    async def do_removal(self, message, limit, predicate):
        deleted = await self.bot.purge_from(message.channel, limit=limit, before=message, check=predicate)
        spammers = Counter(m.author.display_name for m in deleted)
        messages = ['%s %s removed.' % (len(deleted), 'message was' if len(deleted) == 1 else 'messages were')]
        if len(deleted):
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(map(lambda t: '**{0[0]}**: {0[1]}'.format(t), spammers))

        await self.bot.say('\n'.join(messages), delete_after=10)

    @purge.command(pass_context=True)
    async def embeds(self, ctx: commands.context.Context, search=100):
        """Removes messages that have embeds in them."""
        await self.do_removal(ctx.message, search, lambda e: len(e.embeds))

    @purge.command(pass_context=True)
    async def files(self, ctx: commands.context.Context, search=100):
        """Removes messages that have attachments in them."""
        await self.do_removal(ctx.message, search, lambda e: len(e.attachments))

    @purge.command(pass_context=True)
    async def images(self, ctx: commands.context.Context, search=100):
        """Removes messages that have embeds or attachments."""
        await self.do_removal(ctx.message, search, lambda e: len(e.embeds) or len(e.attachments))

    @purge.command(name='all', pass_context=True)
    async def _remove_all(self, ctx: commands.context.Context, search=100):
        """Removes all messages."""
        await self.do_removal(ctx.message, search, lambda e: True)

    @purge.command(pass_context=True)
    async def user(self, ctx: commands.context.Context, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await self.do_removal(ctx.message, search, lambda e: e.author == member)

    @purge.command(pass_context=True)
    async def contains(self, ctx: commands.context.Context, *, substr: str):
        """Removes all messages containing a substring.

        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await self.bot.say('The substring length must be at least 3 characters.')
            return

        await self.do_removal(ctx.message, 100, lambda e: substr in e.content)

    @purge.command(name='bot', pass_context=True)
    async def _bot(self, ctx: commands.context.Context, prefix, *, member: discord.Member):
        """Removes a bot user's messages and messages with their prefix.

        The member doesn't have to have the [Bot] tag to qualify for removal.
        """

        def predicate(m):
            return m.author == member or m.content.startswith(prefix)

        await self.do_removal(ctx.message, 100, predicate)


def setup(bot):
    bot.add_cog(Mod(bot))
