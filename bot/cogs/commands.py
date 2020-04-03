import datetime

import discord
from discord.ext import commands

from bot import RustBot


class Commands(commands.Cog):
    def __init__(self, bot: RustBot):
        self.bot = bot

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
            content="Uptime: {}".format(
                fmt.format(d=days, h=hours, m=minutes, s=seconds)
            )
        )

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Points the user to the #informational channel,
        which contains invite links.
        """

        channel = "<#273547351929520129>"
        link = "https://discordapp.com/channels/273534239310479360/273547351929520129/288101969980162049"
        await ctx.send(f"Invite links are provided in {channel}\n{link}")

    @commands.command(aliases=["wustify"])
    @commands.guild_only()
    async def rustify(self, ctx: commands.Context, *members: discord.Member):
        """Adds the Rustacean role to a member.
        Takes in a space-separated list of member mentions and/or IDs.
        """

        for member in members:
            await member.add_roles(
                self.bot.role.rustacean,
                reason=f"You have been rusted by {ctx.author}! owo",
            )

        await ctx.message.add_reaction(self.bot.emoji.ok)

    @commands.command()
    async def cleanup(self, ctx: commands.Context, limit=None):
        """Deletes the bot's messages for cleanup.
        You can specify how many messages to look for.
        """

        limit = limit or 100

        def is_me(m):
            return m.author.id == self.bot.user.id

        deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @commands.command()
    async def source(self, ctx: commands.Context):
        """Links to the bot GitHub repo."""

        await ctx.send("https://github.com/ivandardi/RustbotPython")

    @commands.command()
    async def ban(self, ctx: commands.Context, member: discord.Member):
        """Bans another person."""
        await ctx.send(f"{ctx.author} banned user {member.mention}  <:ferrisBanne:419884768256327680>")
        await ctx.message.add_reaction(self.bot.emoji.ok)

    async def cog_command_error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Commands(bot))
