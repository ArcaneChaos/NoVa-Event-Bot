import discord
from utils import db, err
import logging

class RSVPModal(discord.ui.Modal):
    def __init__(self, event_id: int):
        super().__init__(title="✅ RSVP & Reminder")
        self.event_id = event_id
        self.logger = logging.getLogger("nova")

        self.reminder_input = discord.ui.InputText(
            label="Reminder time in hours (2–168):",
            placeholder="Leave blank for no reminder",
            required=False
        )

        self.add_item(self.reminder_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            name = interaction.user.display_name
            user_id = str(interaction.user.id)
            reminder_raw = self.reminder_input.value.strip()
            self.logger.debug(f"[RSVPModal] Raw input from {name}: '{reminder_raw}'")

            reminder_minutes = None
            hours = None

            if reminder_raw:
                try:
                    hours = float(reminder_raw)
                    if not (1 <= hours <= 168):
                        raise ValueError("Out of bounds")
                    reminder_minutes = int(hours * 60)
                    self.logger.debug(f"[RSVPModal] Reminder: {reminder_minutes} minutes")
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid reminder time. Use a number between 1 and 168.",
                        ephemeral=True
                    )
                    return

            db.set_rsvp(self.event_id, name, "yes", reminder_minutes, user_id)
            self.logger.info(f"[RSVPModal] RSVP saved for {name}: {reminder_minutes} min")

            await interaction.response.send_message(
                f"✅ RSVP saved! Reminder in **{hours} hours**." if reminder_minutes else "✅ RSVP saved — no reminder set.",
                ephemeral=True
            )

        except Exception as e:
            err.log_error("rsvp.callback", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error("❌ Failed to process RSVP."),
                ephemeral=True
            )
