import discord
from discord.ext import commands
from tinydb import TinyDB, where

from bot import RustBot


def MessageID(argument):
    try:
        return int(argument, base=10)
    except ValueError:
        raise commands.ConversionError(
            f'"{argument}" is not a valid message ID. Use Developer Mode to get the Copy ID option.')


def requires_pin_whitelist():
    async def predicate(ctx: commands.Context):
        if ctx.guild is None:
            return False

        cog = ctx.bot.get_cog('Pin')

        member_is_in_whitelist = cog.db.search(
            (where("channel_id") == ctx.channel.id) & (where("member_id") == ctx.author.id))

        if not member_is_in_whitelist:
            raise commands.CheckFailure("\N{WARNING SIGN} You're not in the pin whitelist of this channel.")

        return True

    return commands.check(predicate)


class Pin(commands.Cog):
    def __init__(self, bot: RustBot):
        self.bot = bot
        self.db = TinyDB(self.bot.config["databases"]["pins"])

    @commands.group()
    @commands.guild_only()
    async def pin(self, ctx):
        """Commands that allows people that aren't mods to pin message on specified channels."""
        pass

    @pin.group(name="whitelist")
    @commands.has_role("Mod")
    async def pin_whitelist(self, ctx):
        """Commands pertaining to the pin whitelists."""
        pass

    @pin_whitelist.command(name="add")
    async def pin_whitelist_add(self, ctx, member: discord.Member):
        """Adds a person to the pin whitelist of the current channel."""
        self.db.insert({
            "channel_id": ctx.channel.id,
            "member_id": member.id,
        })
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @pin_whitelist.command(name="remove", aliases=["del", "delete", "rm"])
    async def pin_whitelist_remove(self, ctx, member: discord.Member):
        """Removes a person from the pin whitelist of the current channel."""
        self.db.remove((where("channel_id") == ctx.channel.id) & (where("member_id") == member.id))
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @pin.command(name="add")
    @requires_pin_whitelist()
    async def pin_add(self, ctx: commands.Context, message_id: MessageID):
        """Pins a message via message ID.
        To pin a message you should right click on the on a message and then
        click "Copy ID". You must have Developer Mode enabled to get that
        functionality.
        """
        message = await ctx.channel.fetch_message(message_id)
        await message.pin()

    @pin.command(name="remove", aliases=["del", "delete", "rm"])
    @requires_pin_whitelist()
    async def pin_remove(self, ctx: commands.Context, message_id: MessageID):
        """Unpins a message via message ID.
        To unpin a message you should right click on the on a message and then
        click "Copy ID". You must have Developer Mode enabled to get that
        functionality.
        """
        message = await ctx.channel.fetch_message(message_id)
        await message.unpin()

    @pin.command(name="list", aliases=["ls"])
    async def pin_list(self, ctx: commands.Context):
        """Shows a list of the current pin whitelist of this channel."""
        whitelist = self.db.search(where("channel_id"))

        if not whitelist:
            return await ctx.send("It appears that this channel's pin whitelist is empty!")

        pin_whitelist = []
        for row in whitelist:
            member = ctx.guild.get_member(row["member_id"])
            if member:
                pin_whitelist.append(str(member))
        pin_whitelist = "\n".join(pin_whitelist)

        await ctx.send(f"People who can whitelist in this channel:\n{pin_whitelist}")

    async def cog_command_error(self, ctx: commands.Context, error):
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Pin(bot))
