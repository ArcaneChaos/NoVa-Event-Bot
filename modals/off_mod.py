import discord
from utils import db, err, time
import os

class OfflinePlayerModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="👤 Add Offline Player")

        self.name_input = discord.ui.InputText(
            label="In-game Name",
            placeholder="e.g. ShadowKing23"
        )
        self.tz_input = discord.ui.InputText(
            label="Timezone (e.g. CST, America/New_York)",
            placeholder="e.g. UTC or eastern or central"
        )
        self.start_input = discord.ui.InputText(
            label="Start of Playtime Window (e.g. 17:00 or 5pm)"
        )
        self.end_input = discord.ui.InputText(
            label="End of Playtime Window (e.g. 22:00 or 10pm)"
        )

        self.add_item(self.name_input)
        self.add_item(self.tz_input)
        self.add_item(self.start_input)
        self.add_item(self.end_input)

    async def callback(self, interaction: discord.Interaction):
        try:
            print("🔔 OfflinePlayerModal.callback triggered")

            name = self.name_input.value.strip()
            tz_raw = self.tz_input.value.strip()
            start = self.start_input.value.strip()
            end = self.end_input.value.strip()

            print(f"👤 name={name}, tz={tz_raw}, start={start}, end={end}")

            if not name:
                raise ValueError("Player name is required.")

            norm_tz = time.normalize_timezone(tz_raw)
            time.parse_time_string(start)
            time.parse_time_string(end)

            db.set_player_time(name, norm_tz, start, end)
            print("✅ set_player_time() call completed")

            await interaction.response.send_message(
                f"✅ Time saved for offline player **{name}**.",
                ephemeral=True
            )

        except Exception as e:
            print("❌ Exception in OfflinePlayerModal.callback:", e)
            err.log_error("off_mod.callback", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error(
                    "❌ Could not save offline time.\n"
                    "- Timezone must be valid (e.g. UTC, central, etc.)\n"
                    "- Times must be readable (e.g. 16:00, 4pm)"
                ),
                ephemeral=True
            )
