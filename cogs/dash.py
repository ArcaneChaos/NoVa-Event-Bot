import discord
from discord.ext import commands
from utils import db, err, auth, time
from modals import time_mod, evt_mod, off_mod, rsvp, crev
import logging
from collections import defaultdict
from datetime import datetime

class DashboardView(discord.ui.View):
    def __init__(self, bot: commands.Bot, events: list[dict], index: int, user_tz: str, is_example_role_id: bool, viewer: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.events = events
        self.index = index if events else -1
        self.user_tz = user_tz
        self.is_example_role_id = is_example_role_id
        self.viewer = viewer
        self.logger = logging.getLogger("nova")
        self.user_event_index = {}  # Track per-user current event view

        # Always add general buttons
        self.add_item(MyTimeButton())
        self.add_item(BestTimeButton())
        self.add_item(HelpButton())

        # Add example_role_id-only global buttons
        if self.is_example_role_id:
            self.add_item(OfflinePlayerButton())
            self.add_item(DeleteOfflineButton())
            self.add_item(CreateEventButton())

        # Add event-related buttons if events exist
        if self.events:
           self.add_item(PrevEventButton())
           self.add_item(NextEventButton())
           self.add_item(RSVPButton())
        if self.is_example_role_id:
           self.add_item(ModifyEventButton())
           self.add_item(DeleteEventButton())


    @property
    def current_event(self):
        if not (0 <= self.index < len(self.events)):
            return None
        return self.events[self.index]

    async def on_timeout(self):
        try:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)
            await self.message.delete()
            self.logger.info(f"🔁 DashboardView expired for event {self.current_event['id']}")
        except Exception:
            pass

    def format_event_text(self):
        if not self.current_event:
            return """```Welcome to the NoVa bot dashboard!\nThere are currently no events scheduled.```"""

        event = self.current_event
        utc_time = event["datetime_utc"]
        local_time = "N/A"
        try:
            if self.user_tz:
                dt = datetime.strptime(utc_time, "%Y-%m-%d %H:%M")
                local_time = time.utc_to_local(dt, self.user_tz)
        except Exception as e:
            err.log_error("dash.timeconvert", e)

        rsvp_count = db.count_rsvps(event["id"])
        rsvp_status = db.get_rsvp(event["id"], self.viewer)
        minutes = db.get_reminder_minutes(event["id"], self.viewer)

        status = "❌ You have not RSVP'd."
        if rsvp_status == "yes" and minutes:
            hrs = round(minutes / 60, 1)
            status = f"✅ You are RSVP'd — reminder in **{hrs} hours**."
        elif rsvp_status == "yes":
            status = "✅ You are RSVP'd — no reminder set."

        return f"""```markdown
📅 Event: {event['title']}
🕒 UTC: {utc_time}
🕒 Your Time: {local_time}
📌 Description: {event['description']}
✅ RSVPs: {rsvp_count}
{status}
```"""

# --- Buttons ---

class PrevEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="◀️ Prev", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view: DashboardView = self.view
        user_id = str(interaction.user.id)
        view.index = (view.index - 1) % len(view.events)
        view.user_event_index[user_id] = view.index
        await interaction.response.edit_message(content=view.format_event_text(), view=view)

class BestTimeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="📊 View Best Times", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        try:
            availability = db.get_all_player_availability()
            if not availability:
                return await interaction.response.send_message(
                    "❌ Not enough player data.", ephemeral=True
                )

            # Track unique players per hour
            hour_bins = [set() for _ in range(24)]
            for player in availability:
                name = player["player_name"]
                tz = player["timezone"]
                start = player["availability_start"]
                end = player["availability_end"]

                try:
                    start_utc = time.local_to_utc(start, tz)
                    end_utc = time.local_to_utc(end, tz)
                except Exception:
                    continue

                start_hour = start_utc.hour
                end_hour = end_utc.hour

                current = start_hour
                while True:
                    hour_bins[current].add(name)
                    current = (current + 1) % 24
                    if current == end_hour:
                        break

            # Combine into 2-hour bins using set unions
            bin_sets = {}
            for h in range(24):
                h1, h2 = h, (h + 1) % 24
                label = f"{h:02d}:00–{(h + 2) % 24:02d}:00"
                players = hour_bins[h1] | hour_bins[h2]
                bin_sets[label] = players

            top = sorted(bin_sets.items(), key=lambda kv: len(kv[1]), reverse=True)[:6]
            max_count = max(1, len(top[0][1])) if top else 1

            output = "🧠 **Best Event Times (UTC):**\n\n"
            for label, players in top:
                count = len(players)
                bars = "░" * int((count / max_count) * 15)
                output += f"`{label}` → {bars:<15} {count} players\n"

            await interaction.response.send_message(output, ephemeral=True)

        except Exception as e:
            err.log_error("dash.besttime_button", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error("❌ Failed to analyze player data."),
                ephemeral=True
            )

class DeleteOfflineDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        for player in db.get_all_player_availability():
            if not player["player_name"].isdigit():
                options.append(discord.SelectOption(label=player["player_name"]))
        if not options:
            options = [discord.SelectOption(label="No offline players", value="none", default=True)]

        super().__init__(placeholder="Select offline player to delete", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            if self.values[0] == "none":
                await interaction.response.send_message("❌ No offline players to delete.", ephemeral=True)
                return

            player_name = self.values[0]
            db.delete_offline_player(player_name)
            await interaction.response.send_message(f"🗑️ Deleted offline player **{player_name}**.", ephemeral=True)
        except Exception as e:
            err.log_error("dash.delete_offline_dropdown", e, include_trace=True)
            await interaction.response.send_message("❌ Could not delete player.", ephemeral=True)

class DeleteOfflineView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(DeleteOfflineDropdown())

class DeleteOfflineButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🗑️ Delete Offline Player", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if not await auth.require_example_role_id(interaction):
            return
        try:
            await interaction.response.send_message("Select a player to delete:", view=DeleteOfflineView(), ephemeral=True)
        except Exception as e:
            err.log_error("dash.delete_offline_button", e)
            await interaction.response.send_message("❌ Could not load player list.", ephemeral=True)

class NextEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="▶️ Next", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view: DashboardView = self.view
        user_id = str(interaction.user.id)
        view.index = (view.index + 1) % len(view.events)
        view.user_event_index[user_id] = view.index
        await interaction.response.edit_message(content=view.format_event_text(), view=view)

class RSVPButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✅ RSVP", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        try:
            name = interaction.user.display_name
            user_id = str(interaction.user.id)
            view: DashboardView = self.view
            idx = view.user_event_index.get(user_id, view.index)
            event_id = view.events[idx]["id"]
            current = db.get_rsvp(event_id, name)

            if current == "yes":
                db.set_rsvp(event_id, name, "no", None, str(interaction.user.id))
                await interaction.response.send_message(
                    "❌ RSVP canceled. You won’t get a reminder.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_modal(rsvp.RSVPModal(event_id))

        except Exception as e:
            err.log_error("dash.rsvp_button", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error("Could not process RSVP."),
                ephemeral=True
            )

class MyTimeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🕒 Set My Time", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(time_mod.SetTimeModal())
        except Exception as e:
            err.log_error("dash.my_time_button", e)
            await interaction.response.send_message(err.user_error("Could not open time modal."), ephemeral=True)

class HelpButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❓ Help", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
    """🛠 **NoVa Event Bot Help**

Use the buttons below each event:

✅ **RSVP** — Sign up for the event and set an optional reminder (1–168 hours before start).

🕒 **Set My Time** — Set your timezone and regular play window so events can be scheduled when most players are active.

📊 **View Best Times** — Shows the best suggested UTC times based on all players' availability.

◀️ ▶️ **Prev / Next** — Navigate between upcoming events.

—

**example_role_id-Only Buttons:**

➕ Create Event — Add a new event using UTC time

📝 Modify — Edit an existing event's time or description

🗑️ Delete — Remove the currently selected event

👤 Set Offline Player Time — Manually set time data for players not on Discord

🗑️ Delete Offline Player — Remove an offline player from the system
""",
    ephemeral=True
)

class ModifyEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="📝 Modify", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if not await auth.require_example_role_id(interaction):
            return
        try:
            user_id = str(interaction.user.id)
            view: DashboardView = self.view
            idx = view.user_event_index.get(user_id, view.index)
            event_id = view.events[idx]["id"]
            await interaction.response.send_modal(evt_mod.EditEventModal(event_id))
        except Exception as e:
            err.log_error("dash.modify_event", e, include_trace=True)
            await interaction.response.send_message(err.user_error("❌ Could not open edit modal."), ephemeral=True)

class CreateEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="➕ Create Event", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        if not await auth.require_example_role_id(interaction):
            return
        await interaction.response.send_modal(crev.CreateEventModal())

class DeleteEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🗑️ Delete", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if not await auth.require_example_role_id(interaction):
            return
        try:
            view: DashboardView = self.view
            event_id = view.current_event["id"]
            db.delete_event(event_id)

            events = db.get_all_events()
            if not events:
                await interaction.response.edit_message(
                    content="❌ Event deleted. No more events scheduled.",
                    view=None
                )
                return

            new_view = DashboardView(
                bot=view.bot,
                events=events,
                index=0,
                user_tz=view.user_tz,
                is_example_role_id=view.is_example_role_id,
                viewer=view.viewer
            )
            await interaction.response.edit_message(
                content=new_view.format_event_text(),
                view=new_view
            )

        except Exception as e:
            err.log_error("dash.delete_event", e, include_trace=True)
            await interaction.response.send_message(
                err.user_error("❌ Could not delete the event."),
                ephemeral=True
            )

class OfflinePlayerButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="👤 Set Offline Player Time", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if not await auth.require_example_role_id(interaction):
            return
        try:
            await interaction.response.send_modal(off_mod.OfflinePlayerModal())
        except Exception as e:
            err.log_error("dash.offline_player_button", e)
            await interaction.response.send_message(err.user_error("Could not open offline modal."), ephemeral=True)

# --- Cog ---

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="novabot", description="Launch event dashboard.")
    async def novabot(self, ctx: discord.ApplicationContext):
        try:
            events = db.get_all_events()
            user_tz = db.get_player_timezone(ctx.user.display_name)
            is_example_role_id = await auth.is_example_role_id(ctx)

            index = 0 if events else -1  # ← use this properly
            view = DashboardView(self.bot, events, index, user_tz, is_example_role_id, ctx.user.display_name)
            view.user_event_index[str(ctx.user.id)] = index
            message = await ctx.respond(view.format_event_text(), view=view)
            view.message = await message.original_response()

        except Exception as e:
            err.log_error("dash.novabot", e, include_trace=True)
            await ctx.respond(err.user_error("Failed to load dashboard."), ephemeral=True)


def setup(bot):
    bot.add_cog(Dashboard(bot))
