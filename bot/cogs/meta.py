import asyncio
import datetime
import re

import discord
from discord.ext import commands


class TimeParser:
    def __init__(self, argument):
        compiled = re.compile(r'(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?')
        self.original = argument
        try:
            self.seconds = int(argument)
        except ValueError as e:
            match = compiled.match(argument)
            if match is None or not match.group(0):
                raise commands.BadArgument('Failed to parse time.') from e

            self.seconds = 0
            hours = match.group('hours')
            if hours is not None:
                self.seconds += int(hours) * 3600
            minutes = match.group('minutes')
            if minutes is not None:
                self.seconds += int(minutes) * 60
            seconds = match.group('seconds')
            if seconds is not None:
                self.seconds += int(seconds)

        if self.seconds < 0:
            raise commands.BadArgument("I don't do negative time.")

        if self.seconds > 604800:  # 7 days
            raise commands.BadArgument("That's a bit too far in the future for me.")


class Meta:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for"""

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        await ctx.send(content='Uptime: **{}**'.format(fmt.format(d=days, h=hours, m=minutes, s=seconds)))

    @commands.command(aliases=['reminder', 'remind'])
    async def timer(self, ctx: commands.Context, time: TimeParser, *, message=''):
        """Reminds you of something after a certain amount of time.
        The time can optionally be specified with units such as 'h'
        for hours, 'm' for minutes and 's' for seconds. If no unit
        is given then it is assumed to be seconds. You can also combine
        multiple units together, e.g. 2h4m10s.
        """

        author = ctx.message.author
        message = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')

        if not message:
            reminder = "Okay {0.mention}, I'll remind you in {1.seconds} seconds."
            completed = 'Time is up {0.mention}! You asked to be reminded about something.'
        else:
            reminder = '''Okay {0.mention}, I'll remind you about "{2}" in {1.seconds} seconds.'''
            completed = 'Time is up {0.mention}! You asked to be reminded about "{1}".'

        await ctx.send(reminder.format(author, time, message))
        await asyncio.sleep(time.seconds)
        await ctx.send(completed.format(author, message))

    @commands.command()
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, *, member: discord.Member = None):
        """Shows info about a member.
        This cannot be used in private messages. If you don't specify
        a member then the info returned will be yours.
        """
        channel = ctx.channel
        if member is None:
            member = ctx.author

        e = discord.Embed()

        roles = [role.name.replace('@', '@\u200b') for role in member.roles]

        e.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        e.set_footer(text='Member since').timestamp = member.joined_at
        e.add_field(name='ID', value=member.id)
        e.add_field(name='Current Name', value=member.display_name)
        e.add_field(name='Created', value=member.created_at)
        e.add_field(name='Roles', value=', '.join(roles))
        e.colour = member.colour

        if member.avatar:
            e.set_image(url=member.avatar_url)

        await ctx.send(embed=e)

    @commands.command()
    async def cleanup(self, ctx: commands.Context, limit=100):
        """Deletes the bot's messages up to the most 100 recent messages."""

        if limit > 100:
            raise commands.BadArgument('Limit is too high!')

        def is_me(m):
            return m.author.id == self.bot.user.id

        deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)


def setup(bot):
    bot.add_cog(Meta(bot))
