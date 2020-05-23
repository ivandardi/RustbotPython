import discord
from discord.ext import commands
from tinydb import where, TinyDB

from bot import RustBot


def is_in_feeds_whitelist(ctx: commands.Context):
    if ctx.guild is None:
        return False

    cog = ctx.bot.get_cog("Feeds")

    member_is_in_whitelist = cog.db.table("whitelist").search(
        (where("channel_id") == ctx.channel.id) & (where("member_id") == ctx.author.id)
    )

    if not member_is_in_whitelist:
        raise commands.CheckFailure(
            "\N{WARNING SIGN} You're not in the feeds whitelist of this channel."
        )

    return True


class Feeds(commands.Cog):
    """A feed is a role that people can subscribe to and get pinged whenever someone publishes something to that
    feed. """

    def __init__(self, bot: RustBot):
        self.bot = bot
        self.db = TinyDB(self.bot.config["databases"]["feeds"])

    async def get_feeds(self, channel_id):
        feeds = self.db.table("feeds").search(where("channel_id") == channel_id)
        return {f["name"]: f["role_id"] for f in feeds}

    @commands.group(name="feeds", aliases=["feed"], invoke_without_command=True)
    @commands.guild_only()
    async def _feeds(self, ctx):
        """Shows the list of feeds that the channel has.
        A feed is something that users can opt-in to
        to receive news about a certain feed by running
        the `sub` command (and opt-out by doing the `unsub` command).
        You can publish to a feed by using the `publish` command.
        """

        feeds = await self.get_feeds(ctx.channel.id)

        if len(feeds) == 0:
            return await ctx.send("This channel has no feeds.")

        names = "\n".join(f"- {r}" for r in feeds)
        await ctx.send(f"Found {len(feeds)} feeds.\n{names}")

    @_feeds.group(name="whitelist", invoke_without_command=True)
    async def _feeds_whitelist(self, ctx: commands.Context):
        """Shows a list of the current feeds whitelist of this channel."""
        whitelist = self.db.table("whitelist").search(
            where("channel_id") == ctx.channel.id
        )

        if not whitelist:
            return await ctx.send(
                "It appears that this channel's feeds whitelist is empty!"
            )

        feeds_whitelist = []
        for row in whitelist:
            member = ctx.guild.get_member(row["member_id"])
            if member:
                feeds_whitelist.append(str(member))
        feeds_whitelist = "\n".join(feeds_whitelist)

        await ctx.send(
            f"People who can publish in a feed in this channel:\n{feeds_whitelist}"
        )

    @_feeds_whitelist.command(name="add")
    async def feeds_whitelist_add(self, ctx: commands.Context, member: discord.Member):
        """Adds a person to the feeds whitelist of the current channel."""
        self.db.table("whitelist").insert(
            {"channel_id": ctx.channel.id, "member_id": member.id,}
        )
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @_feeds_whitelist.command(name="remove", aliases=["del", "delete", "rm"])
    async def feeds_whitelist_remove(self, ctx, member: discord.Member):
        """Removes a person from the feeds whitelist of the current channel."""
        self.db.table("whitelist").remove(
            (where("channel_id") == ctx.channel.id) & (where("member_id") == member.id)
        )
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @_feeds.command(name="create")
    @commands.check_any(
        commands.has_permissions(manage_roles=True), is_in_feeds_whitelist
    )
    async def feeds_create(self, ctx, *, name: str):
        """Creates a feed with the specified name."""

        name = name.lower()

        if name in ("@everyone", "@here"):
            return await ctx.send("That is an invalid feed name.")

        exists = [
            f["role_id"]
            for f in self.db.table("feeds").search(
                (where("channel_id") == ctx.channel.id) & (where("name") == name)
            )
        ]
        if exists:
            return await ctx.send("This feed already exists.")

        role = await ctx.guild.create_role(
            name=name + " feed", permissions=discord.Permissions.none()
        )
        self.db.table("feeds").insert(
            {"name": name, "role_id": role.id, "channel_id": ctx.channel.id}
        )

        await ctx.message.add_reaction(self.bot.emoji.ok)

    @_feeds.command(name="delete", aliases=["remove"])
    @commands.check_any(
        commands.has_permissions(manage_roles=True), is_in_feeds_whitelist
    )
    async def feeds_delete(self, ctx, *, feed: str):
        """Removes a feed from the channel.
        This will also delete the associated role so this
        action is irreversible.
        """

        query = (where("channel_id") == ctx.channel.id) & (where("name") == feed)
        records = self.db.table("feeds").search(query)

        if len(records) == 0:
            return await ctx.send("This feed does not exist.")

        self.db.table("feeds").remove(query)

        for record in records:
            role = discord.utils.find(
                lambda r: r.id == record["role_id"], ctx.guild.roles
            )
            if role is not None:
                try:
                    await role.delete()
                except discord.HTTPException:
                    continue

        await ctx.message.add_reaction(self.bot.emoji.ok)

    @commands.command()
    @commands.guild_only()
    async def sub(self, ctx, *, feed: str):
        """Subscribes to the publication of a feed.
        This will allow you to receive updates from the channel
        owner. To unsubscribe, see the `unsub` command.
        """
        await self.do_subscription(ctx, feed, ctx.author.add_roles)
        await ctx.message.add_reaction(self.bot.emoji.ok)

    @commands.command()
    @commands.guild_only()
    async def unsub(self, ctx, *, feed: str):
        """Unsubscribe to the publication of a feed.
        This will remove you from notifications of a feed you
        are no longer interested in. You can always sub back by
        using the `sub` command.
        """
        await self.do_subscription(ctx, feed, ctx.author.remove_roles)
        await ctx.message.add_reaction(self.bot.emoji.ok)

    async def do_subscription(self, ctx, feed, action):
        feeds = await self.get_feeds(ctx.channel.id)
        if len(feeds) == 0:
            return await ctx.send("This channel has no feeds set up.")

        if feed not in feeds:
            return await ctx.send(
                f'This feed does not exist.\nValid feeds: {", ".join(feeds)}'
            )

        role_id = feeds[feed]
        role = discord.utils.find(lambda r: r.id == role_id, ctx.guild.roles)
        if role is not None:
            await action(role)
            await ctx.message.add_reaction(self.bot.emoji.ok)
        else:
            await ctx.message.add_reaction("❌")

    @commands.command()
    @commands.check_any(
        commands.has_permissions(manage_roles=True), is_in_feeds_whitelist
    )
    @commands.guild_only()
    async def publish(self, ctx, feed: str, *, content: str):
        """Publishes content to a feed.
        Everyone who is subscribed to the feed will be notified
        with the content. Use this to notify people of important
        events or changes.
        """
        feeds = await self.get_feeds(ctx.channel.id)
        feed = feed.lower()
        if feed not in feeds:
            return await ctx.send("This feed does not exist.")

        role = discord.utils.get(ctx.guild.roles, id=feeds[feed])
        if role is None:
            fmt = (
                "Uh... a fatal error occurred here. The role associated with "
                "this feed has been removed or not found. "
                "Please recreate the feed."
            )
            return await ctx.send(fmt)

        # delete the message we used to invoke it
        try:
            await ctx.message.delete()
        except:
            pass

        # make the role mentionable
        await role.edit(mentionable=True)

        # then send the message..
        await ctx.send(f"{role.mention}: {content}"[:2000])

        # then make the role unmentionable
        await role.edit(mentionable=False)


def setup(bot):
    bot.add_cog(Feeds(bot))
