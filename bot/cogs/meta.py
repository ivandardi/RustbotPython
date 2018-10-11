import datetime

import discord
from discord.ext import commands


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

    @commands.command(aliases=["wustify"])
    @commands.guild_only()
    async def rustify(self, ctx: commands.Context, *members: discord.Member):
        """Adds the Rustacean role to a member.
        Takes in a space-separated list of member mentions and/or IDs.
        """
        if not self.rustacean_role:
            self.rustacean_role = discord.utils.get(
                ctx.guild.roles, id=319_953_207_193_501_696
            )
        if not self.bot.emoji_rustok:
            self.bot.log.info("Loading the rustOk emoji...")
            self.bot.emoji_rustok = discord.utils.get(self.bot.emojis, name="rustOk")
        if self.rustacean_role not in ctx.author.roles:
            return await ctx.message.add_reaction("❌")
        for member in members:
            await member.add_roles(
                self.rustacean_role, reason=f"You have been rusted by {ctx.author}! owo"
            )
        await ctx.message.add_reaction(self.bot.emoji_rustok)

    @commands.command()
    async def cleanup(self, ctx: commands.Context, limit=100):
        """Deletes the bot's messages for cleanup.
        You can specify how many messages to look for.
        """

        def is_me(m):
            return m.author.id == self.bot.user.id

        deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await ctx.send(f"Deleted {len(deleted)} message(s)", delete_after=5)

    async def __after_invoke(self, ctx: commands.Context):
        await ctx.message.add_reaction(self.bot.emoji_rustok)

    async def __error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Meta(bot))
