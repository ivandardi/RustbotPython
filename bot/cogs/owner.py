import discord
from discord.ext import commands


class Owner:
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def close(self, ctx: commands.Context):
        """Closes the bot safely. Can only be used by the owner."""
        await self.bot.logout()

    @commands.command()
    @commands.is_owner()
    async def status(self, ctx: commands.Context, *, status: str):
        """Changes the bot's status. Can only be used by the owner."""
        await self.bot.change_presence(activity=discord.Game(name=status))

    @commands.command(name="reload")
    @commands.is_owner()
    async def _reload(self, ctx, *, ext: str = None):
        """Reloads a module. Can only be used by the owner."""

        if ext:
            self.bot.unload_extension(ext)
            self.bot.load_extension(ext)
        else:
            for m in self.bot.initial_extensions:
                self.bot.unload_extension(m)
                self.bot.load_extension(m)

        await ctx.message.add_reaction(self.bot.emoji_rustok)


def setup(bot):
    bot.add_cog(Owner(bot))
