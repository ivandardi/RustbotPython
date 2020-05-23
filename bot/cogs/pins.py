import discord
from discord.ext import commands
from tinydb import TinyDB, where

from bot import RustBot


def MessageID(argument):
    try:
        return int(argument, base=10)
    except ValueError:
        raise commands.ConversionError(
            f'"{argument}" is not a valid message ID. Use Developer Mode to get the Copy ID option.'
        )


def is_in_pin_whitelist(ctx: commands.Context):
    if ctx.guild is None:
        return False

    cog = ctx.bot.get_cog("Pins")

    member_is_in_whitelist = cog.db.search(
        (where("channel_id") == ctx.channel.id) & (where("member_id") == ctx.author.id)
    )

    if not member_is_in_whitelist:
        raise commands.CheckFailure(
            "\N{WARNING SIGN} You're not in the pin whitelist of this channel."
        )

    return True


class Pins(commands.Cog):
    """Commands that allows people that aren't mods to pin message on specified channels."""

    def __init__(self, bot: RustBot):
        self.bot = bot
        self.db = TinyDB(self.bot.config["databases"]["pins"])

    @commands.group(name="pins")
    @commands.guild_only()
    async def _pins(self, ctx):
        """Pin whitelist related commands."""
        await ctx.send("Type `?help Pins` for more help.")

    @_pins.group(name="whitelist", invoke_without_command=True)
    async def _pins_whitelist(self, ctx):
        """Shows a list of the current pin whitelist of this channel."""
        whitelist = self.db.search(where("channel_id") == ctx.channel.id)

        if not whitelist:
            return await ctx.send(
                "It appears that this channel's pin whitelist is empty!"
            )

        pin_whitelist = []
        for row in whitelist:
            member = ctx.guild.get_member(row["member_id"])
            if member:
                pin_whitelist.append(str(member))
        pin_whitelist = "\n".join(pin_whitelist)

        await ctx.send(f"People who can pin messages in this channel:\n{pin_whitelist}")

    @_pins_whitelist.command(name="add")
    @commands.has_role("Mod")
    async def pin_whitelist_add(self, ctx, member: discord.Member):
        """Adds a person to the pin whitelist of the current channel."""
        self.db.insert(
            {"channel_id": ctx.channel.id, "member_id": member.id,}
        )
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @_pins_whitelist.command(name="remove", aliases=["del", "delete", "rm"])
    @commands.has_role("Mod")
    async def pin_whitelist_remove(self, ctx, member: discord.Member):
        """Removes a person from the pin whitelist of the current channel."""
        self.db.remove(
            (where("channel_id") == ctx.channel.id) & (where("member_id") == member.id)
        )
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @commands.command()
    @commands.check(is_in_pin_whitelist)
    async def pin(self, ctx: commands.Context, message_id: MessageID):
        """Pins a message via message ID.
        To pin a message you should right click on the on a message and then
        click "Copy ID". You must have Developer Mode enabled to get that
        functionality.
        """
        message = await ctx.channel.fetch_message(message_id)
        await message.pin()

    @commands.command()
    @commands.check(is_in_pin_whitelist)
    async def unpin(self, ctx: commands.Context, message_id: MessageID):
        """Unpins a message via message ID.
        To unpin a message you should right click on the on a message and then
        click "Copy ID". You must have Developer Mode enabled to get that
        functionality.
        """
        message = await ctx.channel.fetch_message(message_id)
        await message.unpin()
        await ctx.message.add_reaction(self.bot.emoji.ok)

    async def cog_command_error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Pins(bot))
