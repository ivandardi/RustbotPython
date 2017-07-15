import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Roles:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.roles = None

    async def __before_invoke(self, ctx: commands.Context):
        if not self.roles:
            self.roles = [role for role in ctx.guild.roles if role.name.startswith('rust-')]

    async def __after_invoke(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')

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
        if role in self.roles:
            await ctx.author.add_roles(role)
            log.info('Added role %s to member %s', role, ctx.author)
        else:
            raise commands.BadArgument(f'Role "{role}" not found.')

    @role.command(name='del')
    async def _del(self, ctx: commands.Context, role: discord.Role):
        """Delete a role from your list of visible roles."""
        await ctx.author.remove_roles(role)
        log.info('Removed role %s from member %s', role, ctx.author)

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
