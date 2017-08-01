import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Roles:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.roles = None
        self.rustacean_role = None

    async def __before_invoke(self, ctx: commands.Context):
        if not self.roles:
            await self.bot.wait_until_ready()
            self.roles = [role for role in ctx.guild.roles if role.name.startswith('rust-')]

    async def __after_invoke(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')

    @commands.command()
    @commands.guild_only()
    @commands.has_role('Moderator')
    async def rust(self, ctx: commands.Context, member: discord.Member):
        """Adds the Rustacean role to a member."""
        if not self.rustacean_role:
            self.rustacean_role = discord.utils.get(ctx.guild.roles, id=319953207193501696)
        await member.add_roles(self.rustacean_role)

    @commands.group(aliases=['roles'])
    async def role(self, ctx: commands.Context):
        """Manages your roles.

        By adding a role you'll be able to view the corresponding channel.
        """
        if ctx.invoked_subcommand:
            return

        roles = '\n'.join(sorted(map(str, self.roles)))
        await ctx.send(f'List of available roles:\n```\n{roles}\n```\n'
                       'Add the `rust-overview` role to see all channels.\n'
                       'Type `?help role` for more info about the command.')

    @role.command()
    async def add(self, ctx: commands.Context, role: discord.Role):
        """Add a role to your list of visible roles."""
        await self._role_action(role, ctx.author.add_roles)
        log.info('Added role %s to member %s', role, ctx.author)

    @role.command(name='del')
    async def _del(self, ctx: commands.Context, role: discord.Role):
        """Delete a role from your list of visible roles."""
        self._role_action(role, ctx.author.remove_roles)
        log.info('Removed role %s from member %s', role, ctx.author)

    async def _role_action(self, role, action):
        if role in self.roles:
            await action(role)
        else:
            raise commands.BadArgument(f'Role "{role}" not found.')

    @role.command(name='list')
    async def _list(self, ctx: commands.Context):
        """List all your visible roles."""
        roles = '\n'.join(str(role.name) for role in ctx.author.roles if role.name.startswith('rust-'))

        if roles:
            roles = f'```\n{roles}\n```'
        else:
            roles = "You don't have any visible roles!"

        await ctx.send(f'Your available roles:\n{roles}')


def setup(bot):
    bot.add_cog(Roles(bot))
