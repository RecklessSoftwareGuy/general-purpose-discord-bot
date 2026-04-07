import discord
import io
from functions import database_functions as db


async def create_ticket_channel(guild: discord.Guild, user: discord.Member, category_id: int | None) -> discord.TextChannel | None:
    """Create a private ticket channel for a user."""
    category = guild.get_channel(category_id) if category_id else None

    # Count existing tickets for naming
    open_count = await db.get_user_open_tickets(guild.id, user.id)
    channel_name = f"ticket-{user.name}-{open_count + 1}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }

    # Also allow roles with manage_guild permission to see tickets
    for role in guild.roles:
        if role.permissions.manage_guild:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    try:
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category if isinstance(category, discord.CategoryChannel) else None,
            overwrites=overwrites,
            topic=f"Support ticket for {user.display_name} ({user.id})",
        )
        await db.create_ticket(guild.id, channel.id, user.id)
        return channel
    except discord.Forbidden:
        return None


async def generate_transcript(channel: discord.TextChannel, limit: int = 500) -> io.BytesIO:
    """Generate a plain-text transcript of a ticket channel."""
    lines = []
    lines.append(f"Transcript of #{channel.name}")
    lines.append(f"Generated at: {discord.utils.utcnow().isoformat()}")
    lines.append("=" * 60)
    lines.append("")

    messages = []
    async for message in channel.history(limit=limit, oldest_first=True):
        messages.append(message)

    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content or "[No text content]"
        attachments = ", ".join(a.url for a in msg.attachments) if msg.attachments else ""
        line = f"[{timestamp}] {msg.author.display_name}: {content}"
        if attachments:
            line += f"\n  Attachments: {attachments}"
        lines.append(line)

    text = "\n".join(lines)
    buffer = io.BytesIO(text.encode("utf-8"))
    buffer.seek(0)
    return buffer


async def close_ticket_channel(channel: discord.TextChannel, closer: discord.Member | discord.User) -> io.BytesIO:
    """Close a ticket: generate transcript, update DB, return transcript buffer."""
    transcript = await generate_transcript(channel)
    await db.close_ticket(channel.id)
    return transcript
