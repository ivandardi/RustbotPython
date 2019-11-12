import logging

import discord
from discord.ext import commands

from bot import RustBot

log = logging.getLogger(__name__)


class Votes(commands.Cog):
    def __init__(self, bot: RustBot):
        self.bot = bot

    @commands.Cog.listener("on_raw_reaction_add")
    async def council_votes(self, payload: discord.RawReactionActionEvent):
        is_in_voting_channel = payload.channel_id == self.bot.config["council_channel_id"]
        if not is_in_voting_channel:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        is_council_member = discord.utils.get(member.roles, id=self.bot.role.council.id)
        if not is_council_member:
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)


def setup(bot):
    bot.add_cog(Votes(bot))
