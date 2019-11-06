import discord
from discord.ext import commands
from tinydb import where, TinyDB, JSONStorage

from bot import RustBot


class Feeds(commands.Cog):
    """
    The feeds are stored in a JSON database with the fields:
     * name
     * role_id
     * channel_id
    """

    def __init__(self, bot: RustBot):
        self.bot = bot
        self.db = TinyDB(self.bot.config["feeds_database"])

    async def get_feeds(self, channel_id):
        feeds = self.db.search(where("channel_id") == channel_id)
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

    @_feeds.command(name="create")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def feeds_create(self, ctx, *, name: str):
        """Creates a feed with the specified name.
        You need Manage Roles permissions to create a feed.
        """

        name = name.lower()

        if name in ("@everyone", "@here"):
            return await ctx.send("That is an invalid feed name.")

        exists = [
            f["role_id"]
            for f in self.db.search(
                (where("channel_id") == ctx.channel.id) & (where("name") == name)
            )
        ]
        if exists:
            return await ctx.send("This feed already exists.")

        role = await ctx.guild.create_role(
            name=name, permissions=discord.Permissions.none()
        )
        self.db.insert({"name": name, "role_id": role.id, "channel_id": ctx.channel.id})

        await ctx.send(f"Successfully created feed.")

    @_feeds.command(name="delete", aliases=["remove"])
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def feeds_delete(self, ctx, *, feed: str):
        """Removes a feed from the channel.
        This will also delete the associated role so this
        action is irreversible.
        """

        query = (where("channel_id") == ctx.channel.id) & (where("name") == feed)

        records = self.db.search(query)

        if len(records) == 0:
            return await ctx.send("This feed does not exist.")

        self.db.remove(query)

        for record in records:
            role = discord.utils.find(
                lambda r: r.id == record["role_id"], ctx.guild.roles
            )
            if role is not None:
                try:
                    await role.delete()
                except discord.HTTPException:
                    continue

        await ctx.send(f"Removed feed.")

    @commands.command()
    @commands.guild_only()
    async def sub(self, ctx, *, feed: str):
        """Subscribes to the publication of a feed.
        This will allow you to receive updates from the channel
        owner. To unsubscribe, see the `unsub` command.
        """
        await self.do_subscription(ctx, feed, ctx.author.add_roles)

    @commands.command()
    @commands.guild_only()
    async def unsub(self, ctx, *, feed: str):
        """Unsubscribe to the publication of a feed.
        This will remove you from notifications of a feed you
        are no longer interested in. You can always sub back by
        using the `sub` command.
        """
        await self.do_subscription(ctx, feed, ctx.author.remove_roles)

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
            await ctx.message.add_reaction(self.bot.emoji_rustok)
        else:
            await ctx.message.add_reaction("❌")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
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
