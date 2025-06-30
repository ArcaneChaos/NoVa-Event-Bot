import discord
from utils import db, err, time

class SetTimeModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🕒 Set My Time Preferences")

        self.tz_input = discord.ui.InputText(
            label="Timezone (e.g. CST, UTC, America/New_York)",
            placeholder="central / eastern / UTC / pst / America/Chicago"
        )
        self.start_input = discord.ui.InputText(
            label="Start of Playtime Window (e.g. 17:00 or 5pm)",
            placeholder="Start time"
        )
        self.end_input = discord.ui.InputText(
            label="End of Playtime Window (e.g. 22:00 or 10pm)",
            placeholder="End time"
        )

        self.add_item(self.tz_input)
        self.add_item(self.start_input)
        self.add_item(self.end_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            print("✅ SetTimeModal.callback fired")

            name = interaction.user.display_name
            tz = self.tz_input.value.strip()
            start = self.start_input.value.strip()
            end = self.end_input.value.strip()

            norm_tz = time.normalize_timezone(tz)
            time.parse_time_string(start)
            time.parse_time_string(end)

            db.set_player_time(name, norm_tz, start, end)

            await interaction.response.send_message(
                "✅ Your time preferences have been saved.",
                ephemeral=True
            )

        except Exception as e:
            err.log_error("time_modal.callback", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error(
                    "❌ Could not save your time.\n"
                    "- Timezone must be valid (e.g. `UTC`, `central`, `America/Chicago`)\n"
                    "- Time must be readable (e.g. `16:00`, `4pm`, `0430`)"
                ),
                ephemeral=True
            )
