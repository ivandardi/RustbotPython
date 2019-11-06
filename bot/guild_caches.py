import logging

import discord

log = logging.getLogger(__name__)


class GuildEmojis:
    def __init__(self, emoji_config, discord_emojis):
        for emoji_label, emoji_name in emoji_config.items():
            emoji = discord.utils.get(discord_emojis, name=emoji_name)

            if not emoji:
                log.info("Emoji %s not loaded.", emoji_name)
                continue

            log.info("Emoji %s loaded.", emoji_name)
            setattr(self, emoji_label, emoji)


class GuildRoles:
    def __init__(self, role_config, discord_roles):
        for role_label, role_id in role_config.items():
            role = discord.utils.get(discord_roles, id=role_id)

            if not role:
                log.info("Role %s not loaded.", role_label)
                continue

            log.info("Role %s loaded.", role_label)
            setattr(self, role_label, role)
