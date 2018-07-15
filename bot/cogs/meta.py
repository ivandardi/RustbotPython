import asyncio
import datetime
import re
import random

import discord
from discord.ext import commands


class TimeParser:

        negative_times = [
        "I don't do negative time",
        "Negative time? Time travel? Pfft Marty, that's just silly!",
        "Quick! To the Delorean! ... Oh wait, we don't have one 🤔",
        "NEGATIVE TIME IS UNSAFE 😭",
        "Always positive time pls",
        "NEGATIVE TIME? BAAAAAAAAAAAAAAANNE!",
    ]

    too_big_times = [
        "That's a bit too far in the future for me",
        "If you need to be remembered that far in the future, maaaybe use a calendar?",
        "The limit is 7 days :v",
        "REMINDER IN MORE THAN 7 DAYS? BAAAAAAAAAAAAAANNE!",
    ]

    def __init__(self, argument):
        compiled = re.compile(
            r"(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?"
        )
        self.original = argument
        try:
            self.seconds = int(argument)
        except ValueError as e:
            match = compiled.match(argument)
            if match is None or not match.group(0):
                raise commands.BadArgument("Failed to parse time.") from e

            self.seconds = 0
            days = match.group("days")
            if days is not None:
                self.seconds += int(days) * 86400
            hours = match.group("hours")
            if hours is not None:
                self.seconds += int(hours) * 3600
            minutes = match.group("minutes")
            if minutes is not None:
                self.seconds += int(minutes) * 60
            seconds = match.group("seconds")
            if seconds is not None:
                self.seconds += int(seconds)

        if self.seconds < 0:
            error_msg = random.choice(self.negative_times)
            raise commands.BadArgument(error_msg)

        if self.seconds > 7 * 24 * 60 * 60:  # 7 days
            error_msg = random.choice(self.too_big_times)
            raise commands.BadArgument(error_msg)


class Meta:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rustacean_role = None

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tells you how long the bot has been up for."""

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = "{h}h {m}m {s}s"
        if days:
            fmt = "{d}d " + fmt

        await ctx.send(
            content="Uptime: **{}**".format(
                fmt.format(d=days, h=hours, m=minutes, s=seconds)
            )
        )

    @commands.command(aliases=["reminder", "remind"])
    async def timer(
        self, ctx: commands.Context, time: TimeParser, *, message="something"
    ):
        """Reminds you of something after a certain amount of time.
        The time can optionally be specified with units such as 'h'
        for hours, 'm' for minutes and 's' for seconds. If no unit
        is given then it is assumed to be seconds. You can also combine
        multiple units together, e.g. 2h4m10s.
        The time can optionally be specified with units such as 'd' for days,
        'h' for hours, 'm' for minutes and 's' for seconds.
        If no unit is given then it is assumed to be seconds. You can also
        combine multiple units together, e.g. 3d2h4m10s.
        The maximum time limit is 7 days.
        """

        author = ctx.message.author
        message = message.replace("@everyone", "@\u200beveryone").replace(
            "@here", "@\u200bhere"
        )

        await ctx.send(f"""Okay {author.mention}, I'll remind you about "{message}" in {time.seconds} seconds.""")
        await asyncio.sleep(time.seconds)
        await ctx.send(f'Time is up {author.mention}! You asked to be reminded about "{message}".')

    @commands.command()
    @commands.guild_only()
    async def rustify(self, ctx: commands.Context, *members: discord.Member):
        """Adds the Rustacean role to a member.
        Takes in a list of member mentions and/or IDs.
        """
        if not self.rustacean_role:
            self.rustacean_role = discord.utils.get(
                ctx.guild.roles, id=319953207193501696
            )
        if self.rustacean_role not in ctx.author.roles:
            await ctx.message.add_reaction("❌")
            return
        for member in members:
            await member.add_roles(
                self.rustacean_role, reason="You have been rusted! owo"
            )
        await ctx.message.add_reaction("👌")

    @commands.command()
    async def cleanup(self, ctx: commands.Context, limit=100):
        """Deletes the bot's messages for cleanup. You can specify how many
        messages to look for.
        """

        def is_me(m):
            return m.author.id == self.bot.user.id

        deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)


def setup(bot):
    bot.add_cog(Meta(bot))
