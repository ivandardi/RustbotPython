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

        channel = self.bot.get_channel(payload.channel_id)
        is_council_member = channel.guild.get_role(self.bot.role.council)
        if not is_council_member:
            message = await channel.fetch_message(payload.message_id)
            user = await self.bot.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)


def setup(bot):
    bot.add_cog(Votes(bot))
