import asyncio
import copy
import datetime
import re
from collections import Counter

import discord
from discord.ext import commands

from utils import checks, formats


class TimeParser:
    def __init__(self, argument):
        compiled = re.compile(r"(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?")
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
            raise commands.BadArgument('I don\'t do negative time.')

        if self.seconds > 604800:  # 7 days
            raise commands.BadArgument('That\'s a bit too far in the future for me.')


class Meta:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def uptime(self):
        """Tells you how long the bot has been up for.

        """

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        await self.bot.say(f'Uptime: **{fmt.format(d=days, h=hours, m=minutes, s=seconds)}**')

    @commands.command(pass_context=True, aliases=['reminder', 'remind'])
    async def timer(self, ctx: commands.context.Context, time: TimeParser, *, message=''):
        """Reminds you of something after a certain amount of time.
        The time can optionally be specified with units such as 'h'
        for hours, 'm' for minutes and 's' for seconds. If no unit
        is given then it is assumed to be seconds. You can also combine
        multiple units together, e.g. 2h4m10s.
        """

        author = ctx.message.author
        message = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')

        if not message:
            reminder = 'Okay {0.mention}, I\'ll remind you in {1.seconds} seconds.'
            completed = 'Time is up {0.mention}! You asked to be reminded about something.'
        else:
            reminder = 'Okay {0.mention}, I\'ll remind you about "{2}" in {1.seconds} seconds.'
            completed = 'Time is up {0.mention}! You asked to be reminded about "{1}".'

        await self.bot.say(reminder.format(author, time, message))
        await asyncio.sleep(time.seconds)
        await self.bot.say(completed.format(author, message))

    @timer.error
    async def timer_error(self, error, ctx: commands.context.Context):
        if type(error) is commands.BadArgument:
            await self.bot.say(str(error))

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    async def info(self, ctx, *, member: discord.Member = None):
        """Shows info about a member.
        This cannot be used in private messages. If you don't specify
        a member then the info returned will be yours.
        """
        channel = ctx.message.channel
        if member is None:
            member = ctx.message.author

        e = discord.Embed()
        roles = [role.name.replace('@', '@\u200b') for role in member.roles]
        shared = sum(1 for m in self.bot.get_all_members() if m.id == member.id)
        voice = member.voice_channel
        if voice is not None:
            other_people = len(voice.voice_members) - 1
            voice_fmt = '{} with {} others' if other_people else '{} by themselves'
            voice = voice_fmt.format(voice.name, other_people)
        else:
            voice = 'Not connected.'

        e.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        e.set_footer(text='Member since').timestamp = member.joined_at
        e.add_field(name='ID', value=member.id)
        e.add_field(name='Servers', value='%s shared' % shared)
        e.add_field(name='Voice', value=voice)
        e.add_field(name='Created', value=member.created_at)
        e.add_field(name='Roles', value=', '.join(roles))
        e.colour = member.colour

        if member.avatar:
            e.set_image(url=member.avatar_url)

        await self.bot.say(embed=e)

    @info.command(name='server', pass_context=True, no_pm=True)
    async def server_info(self, ctx: commands.context.Context):
        server = ctx.message.server
        roles = [role.name.replace('@', '@\u200b') for role in server.roles]

        secret_member = copy.copy(server.me)
        secret_member.id = '0'
        secret_member.roles = [server.default_role]

        # figure out what channels are 'secret'
        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in server.channels:
            perms = channel.permissions_for(secret_member)
            is_text = channel.type == discord.ChannelType.text
            text_channels += is_text
            if is_text and not perms.read_messages:
                secret_channels += 1
            elif not is_text and (not perms.connect or not perms.speak):
                secret_voice += 1

        regular_channels = len(server.channels) - secret_channels
        voice_channels = len(server.channels) - text_channels
        member_by_status = Counter(str(m.status) for m in server.members)

        e = discord.Embed()
        e.title = 'Info for ' + server.name
        e.add_field(name='ID', value=server.id)
        e.add_field(name='Owner', value=server.owner)
        if server.icon:
            e.set_thumbnail(url=server.icon_url)

        if server.splash:
            e.set_image(url=server.splash_url)

        e.add_field(name='Partnered?', value='Yes' if server.features else 'No')

        fmt = 'Text %s (%s secret)\nVoice %s (%s locked)'
        e.add_field(name='Channels', value=fmt % (text_channels, secret_channels, voice_channels, secret_voice))

        fmt = 'Total: {0}\nOnline: {1[online]}' \
              ', Offline: {1[offline]}' \
              '\nDnD: {1[dnd]}' \
              ', Idle: {1[idle]}'

        e.add_field(name='Members', value=fmt.format(server.member_count, member_by_status))
        e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else '%s roles' % len(roles))
        e.set_footer(text='Created').timestamp = server.created_at
        await self.bot.say(embed=e)

    async def say_permissions(self, member, channel):
        permissions = channel.permissions_for(member)
        entries = [(attr.replace('_', ' ').title(), val) for attr, val in permissions]
        await formats.entry_to_code(self.bot, entries)

    @commands.command(pass_context=True, no_pm=True)
    async def permissions(self, ctx: commands.context.Context, *, member: discord.Member = None):
        """Shows a member's permissions.
        You cannot use this in private messages. If no member is given then
        the info returned will be yours.
        """
        channel = ctx.message.channel
        if member is None:
            member = ctx.message.author

        await self.say_permissions(member, channel)

    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def botpermissions(self, ctx: commands.context.Context):
        """Shows the bot's permissions.
        This is a good way of checking if the bot has the permissions needed
        to execute the commands it wants to execute.
        To execute this command you must have Manage Roles permissions or
        have the Bot Admin role. You cannot use this in private messages.
        """
        channel = ctx.message.channel
        member = ctx.message.server.me
        await self.say_permissions(member, channel)


def setup(bot):
    bot.add_cog(Meta(bot))
