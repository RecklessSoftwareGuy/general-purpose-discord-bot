import discord
from views import embeds
from functions import ticket_functions as tf


class ConfirmView(discord.ui.View):
    """A simple confirm/cancel view for destructive actions."""
    def __init__(self, author_id: int, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.confirmed: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.edit_message(content="✅ Confirmed.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.edit_message(content="❌ Cancelled.", view=None)


class TicketPanelView(discord.ui.View):
    """Persistent view for the ticket panel. Users click to create a ticket."""
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="ticket_panel_create")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        from functions import database_functions as db

        # Check for existing open tickets
        open_count = await db.get_user_open_tickets(interaction.guild.id, interaction.user.id)
        if open_count >= 3:
            await interaction.response.send_message("❌ You already have 3 open tickets! Please close one first.", ephemeral=True)
            return

        # Get ticket category from config
        config = await db.get_guild_config(interaction.guild.id)
        category_id = config.get("ticket_category_id") if config else None

        channel = await tf.create_ticket_channel(interaction.guild, interaction.user, category_id)
        if channel:
            await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)
            # Send welcome message in the ticket channel
            await channel.send(
                embed=embeds.ticket_created_x0(interaction.user),
                view=TicketControlView()
            )
        else:
            await interaction.response.send_message("❌ Failed to create ticket. I may lack permissions.", ephemeral=True)


class TicketControlView(discord.ui.View):
    """Persistent view inside a ticket channel for close/transcript."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        if not interaction.user.guild_permissions.manage_guild and not interaction.channel:
            await interaction.response.send_message("❌ You lack permission to close this ticket.", ephemeral=True)
            return

        from functions import database_functions as db

        ticket = await db.get_ticket(interaction.channel.id)  # type: ignore
        if not ticket:
            await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
            return

        # Check if the user is the ticket creator or has manage_guild
        if interaction.user.id != ticket["user_id"] and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Only the ticket creator or staff can close this.", ephemeral=True)
            return

        await interaction.response.send_message(embed=embeds.ticket_closed_x0(interaction.user))

        # Generate transcript and close
        if isinstance(interaction.channel, discord.TextChannel):
            transcript = await tf.close_ticket_channel(interaction.channel, interaction.user)

            # Send transcript to log channel
            config = await db.get_guild_config(interaction.guild.id)
            if config and config.get("ticket_log_channel_id"):
                log_channel = interaction.guild.get_channel(config["ticket_log_channel_id"])
                if log_channel and isinstance(log_channel, discord.TextChannel):
                    try:
                        await log_channel.send(
                            f"🎫 Ticket `#{interaction.channel.name}` closed by {interaction.user.mention}",
                            file=discord.File(transcript, filename=f"transcript-{interaction.channel.name}.txt")
                        )
                    except discord.Forbidden:
                        pass

            # Delete the channel after a short delay
            import asyncio
            await asyncio.sleep(3)
            try:
                await interaction.channel.delete(reason="Ticket closed")
            except discord.Forbidden:
                pass

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="ticket_transcript")
    async def get_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.channel, discord.TextChannel):
            return
        await interaction.response.defer(ephemeral=True)
        transcript = await tf.generate_transcript(interaction.channel)
        await interaction.followup.send(
            file=discord.File(transcript, filename=f"transcript-{interaction.channel.name}.txt"),
            ephemeral=True
        )


class HelpView(discord.ui.View):
    """Paginated help view with navigation buttons."""
    def __init__(self, pages: list[discord.Embed], author_id: int, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.current_page <= 0
        self.next_btn.disabled = self.current_page >= len(self.pages) - 1
        self.page_indicator.label = f"{self.current_page + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Use your own help command!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple, custom_id="help_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True, custom_id="help_indicator")
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple, custom_id="help_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="🏠 Home", style=discord.ButtonStyle.green, custom_id="help_home")
    async def home_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[0], view=self)


class GiveawayEntryView(discord.ui.View):
    """Persistent view for giveaway entries."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.green, emoji="🎉", custom_id="giveaway_enter")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # The actual entry is tracked via message reactions, this button just adds the reaction
        try:
            await interaction.message.add_reaction("🎉")  # type: ignore
            await interaction.response.send_message("🎉 You've entered the giveaway!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Failed to enter. Try reacting with 🎉 manually.", ephemeral=True)
