import discord
import time
from functions import database_functions as db


async def process_warning(guild_id: int, user_id: int, moderator_id: int, reason: str) -> tuple[int, int]:
    """Add a warning and return (warning_id, total_warnings_count)."""
    warning_id = await db.add_warning(guild_id, user_id, moderator_id, reason)
    await db.log_mod_action(guild_id, user_id, moderator_id, "warn", reason)
    warnings = await db.get_warnings(guild_id, user_id)
    return warning_id, len(warnings)


async def process_kick(guild_id: int, user_id: int, moderator_id: int, reason: str):
    """Log a kick action."""
    await db.log_mod_action(guild_id, user_id, moderator_id, "kick", reason)


async def process_ban(guild_id: int, user_id: int, moderator_id: int, reason: str, duration: str | None = None):
    """Log a ban action (permanent or temp)."""
    action = "tempban" if duration else "ban"
    await db.log_mod_action(guild_id, user_id, moderator_id, action, reason, duration)


async def process_unban(guild_id: int, user_id: int, moderator_id: int):
    """Log an unban action and remove temp ban entry if exists."""
    await db.log_mod_action(guild_id, user_id, moderator_id, "unban")
    await db.remove_temp_ban(guild_id, user_id)


async def process_mute(guild_id: int, user_id: int, moderator_id: int, reason: str, duration: str):
    """Log a mute action."""
    await db.log_mod_action(guild_id, user_id, moderator_id, "mute", reason, duration)


async def process_unmute(guild_id: int, user_id: int, moderator_id: int):
    """Log an unmute action."""
    await db.log_mod_action(guild_id, user_id, moderator_id, "unmute")


async def send_mod_log(guild: discord.Guild, embed: discord.Embed):
    """Send an embed to the guild's configured mod-log channel."""
    config = await db.get_guild_config(guild.id)
    if config and config.get("mod_log_channel_id"):
        channel = guild.get_channel(config["mod_log_channel_id"])
        if channel and isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass


def build_mod_log_embed(action: str, moderator: discord.Member | discord.User, target: discord.Member | discord.User, reason: str | None = None, duration: str | None = None, extra: str | None = None) -> discord.Embed:
    """Build a standard mod log embed."""
    colours = {
        "warn": discord.Colour.yellow(),
        "mute": discord.Colour.orange(),
        "unmute": discord.Colour.green(),
        "kick": discord.Colour.dark_orange(),
        "ban": discord.Colour.red(),
        "tempban": discord.Colour.dark_red(),
        "unban": discord.Colour.green(),
        "softban": discord.Colour.dark_red(),
    }
    em = discord.Embed(
        title=f"Moderation Action: {action.upper()}",
        colour=colours.get(action, discord.Colour.greyple()),
        timestamp=discord.utils.utcnow()
    )
    em.add_field(name="Target", value=f"{target.mention} (`{target.id}`)", inline=True)
    em.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
    if reason:
        em.add_field(name="Reason", value=reason, inline=False)
    if duration:
        em.add_field(name="Duration", value=duration, inline=True)
    if extra:
        em.add_field(name="Details", value=extra, inline=False)
    em.set_thumbnail(url=target.display_avatar.url)
    em.set_footer(text=f"User ID: {target.id}")
    return em


def format_warnings_list(warnings: list[dict], user: discord.Member | discord.User) -> discord.Embed:
    """Format a list of warnings into a nice embed."""
    em = discord.Embed(
        title=f"Warnings for {user.display_name}",
        description=f"**Total warnings:** {len(warnings)}",
        colour=discord.Colour.yellow()
    )
    if not warnings:
        em.description = f"{user.display_name} has no warnings."
        em.colour = discord.Colour.green()
        return em

    for w in warnings[:25]:  # Discord embed field limit
        em.add_field(
            name=f"Warning #{w['id']}",
            value=f"**Reason:** {w['reason']}\n**By:** <@{w['moderator_id']}>\n**Date:** <t:{w['timestamp']}:R>",
            inline=False
        )
    if len(warnings) > 25:
        em.set_footer(text=f"Showing 25 of {len(warnings)} warnings")
    return em


async def get_moderation_history_embed(guild_id: int, user: discord.Member | discord.User, limit: int = 10) -> discord.Embed:
    """Get a formatted embed of a user's mod history."""
    actions = await db.get_mod_actions(guild_id, user.id, limit)
    em = discord.Embed(
        title=f"Moderation History — {user.display_name}",
        colour=discord.Colour.blurple()
    )
    if not actions:
        em.description = "No moderation history found."
        return em

    for a in actions:
        value = f"**By:** <@{a['moderator_id']}>"
        if a.get("reason"):
            value += f"\n**Reason:** {a['reason']}"
        if a.get("duration"):
            value += f"\n**Duration:** {a['duration']}"
        value += f"\n**Date:** <t:{a['timestamp']}:R>"
        em.add_field(name=f"{a['action'].upper()} (#{a['id']})", value=value, inline=False)
    return em
