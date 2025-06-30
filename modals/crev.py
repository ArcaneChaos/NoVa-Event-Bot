import discord
from utils import db, err
from datetime import datetime
import os

class CreateEventModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📝 Create New Event")

        self.title_input = discord.ui.InputText(
            label="Title",
            placeholder="e.g. Alliance Raid — North Sector",
            max_length=100
        )
        self.time_input = discord.ui.InputText(
            label="UTC Time (YYYY-MM-DD HH:MM)",
            placeholder="e.g. 2025-05-20 01:00"
        )
        self.desc_input = discord.ui.InputText(
            label="Optional Description",
            style=discord.InputTextStyle.long,
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.time_input)
        self.add_item(self.desc_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            print("🔔 CreateEventModal.callback triggered")
            title = self.title_input.value.strip()
            time_str = self.time_input.value.strip()
            desc = self.desc_input.value.strip()

            if not title or not time_str:
                raise ValueError("Title and time are required.")
            if len(title) > 100:
                raise ValueError("Title too long.")

            try:
                datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("Invalid datetime format.")

            db.create_event(title, time_str, desc)

            await interaction.response.send_message(
                "✅ Event created successfully.",
                ephemeral=True
            )

            # 🔔 Notify the main channel
            channel_id = int(os.getenv("REMINDER_CHANNEL_ID", 0))
            channel = interaction.client.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"📅 **New Event Created!**\n**{title}** scheduled for `{time_str}` UTC.\nUse `/novabot` to RSVP."
                )

        except Exception as e:
            err.log_error("create_event.callback", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error(
                    "❌ Could not create event.\n"
                    "- Title and time are required.\n"
                    "- Time format must be `YYYY-MM-DD HH:MM`\n"
                    "- Title must be under 100 characters."
                ),
                ephemeral=True
            )
