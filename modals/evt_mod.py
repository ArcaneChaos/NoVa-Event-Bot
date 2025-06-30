import discord
from utils import db, err
from datetime import datetime
import os

class EditEventModal(discord.ui.Modal):
    def __init__(self, event_id: int):
        super().__init__(title="✏️ Edit Event")
        self.event_id = event_id

        event = db.get_event_by_id(event_id)

        self.title_display = discord.ui.InputText(
            label="(Title, do not attempt to modify)",
            value=event["title"],
            required=False,
            max_length=100,
            style=discord.InputTextStyle.short,
        )

        self.time_input = discord.ui.InputText(
            label="UTC Time (YYYY-MM-DD HH:MM)",
            placeholder="e.g. 2025-05-21 23:00",
            value=event["datetime_utc"]
        )

        self.desc_input = discord.ui.InputText(
            label="Description",
            style=discord.InputTextStyle.long,
            required=False,
            value=event.get("description", "")
        )

        self.add_item(self.title_display)
        self.add_item(self.time_input)
        self.add_item(self.desc_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            print("🔔 EditEventModal.callback triggered")

            time_str = self.time_input.value.strip()
            desc = self.desc_input.value.strip()

            if not time_str:
                raise ValueError("Time is required.")

            try:
                utc_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("Time format must be YYYY-MM-DD HH:MM")

            if utc_dt < datetime.utcnow():
                raise ValueError("Time must be in the future.")

            time_clean = utc_dt.strftime("%Y-%m-%d %H:%M")

            event = db.get_event_by_id(self.event_id)
            title = event["title"]
            old_time = event["datetime_utc"]

            print(f"📌 Updating event {self.event_id}: {title} @ {time_clean}")
            db.update_event(self.event_id, title, time_clean, desc)

            await interaction.response.send_message("✅ Event updated.", ephemeral=True)

            # 🔔 If time changed, notify RSVP'd users
            if old_time != time_clean:
                rsvps = db.get_reminders_due(self.event_id)
                if rsvps:
                    mentions = [f"<@{rsvp['discord_id']}>" for rsvp in rsvps if rsvp ['discord_id']]
                    mention_block = ", ".join(mentions)

                    channel_id = int(os.getenv("REMINDER_CHANNEL_ID", 0))
                    channel = interaction.client.get_channel(channel_id)
                    if channel:
                        await channel.send(
                            f"🔔 **Event Updated**: **{title}**\n"
                            f"🕒 New Time: `{time_clean}` UTC\n"
                            f"{mention_block}"
                        )

        except Exception as e:
            err.log_error("evt_mod.callback", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error(
                    "❌ Event Not Saved.\n"
                    "- Time must be in UTC format: `YYYY-MM-DD HH:MM`\n"
                    "- Time must be in the future."
                ),
                ephemeral=True
            )
