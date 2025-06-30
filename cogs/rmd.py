from datetime import datetime
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils import db, err, time
import os
import logging

scheduler = AsyncIOScheduler()

class ReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("nova")

    def start(self):
        self.bot.scheduler = scheduler  # Expose for cleanup
        scheduler.add_job(self.run_reminders, IntervalTrigger(seconds=120))
        scheduler.start()

    async def run_reminders(self):
        now = datetime.utcnow()
        self.logger.debug(f"[ReminderTick] Scheduler ran at {now.isoformat()}")

        try:
            events = db.get_all_events()
            for event in events:
                event_id = event["id"]
                title = event["title"]
                utc_dt = datetime.strptime(event["datetime_utc"], "%Y-%m-%d %H:%M")
                mins_until = int((utc_dt - now).total_seconds() / 60)

                self.logger.debug(f"[Reminder] Checking event {event_id} → {title} (starts in {mins_until} mins)")

                channel_id = int(os.getenv("REMINDER_CHANNEL_ID", 0))
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    self.logger.warning(f"[Reminder] Channel ID {channel_id} not found.")
                    continue

                # --- Static group reminders ---
                if 59 <= mins_until <= 61:
                    await channel.send(f"🕐 1 hour until **{title}**.")
                elif 29 <= mins_until <=31:
                    await channel.send(f"@everyone ⚔️ **{title}** starts in 30 minutes!")
                elif 14 <= mins_until <= 16:
                    await channel.send(f"🧊 15 minutes until **{title}**. Prep up.")
                elif 1 <= mins_until <= 3:
                    await channel.send(f"@everyone 🚨 **{title}** starts NOW!")

                # --- Personal RSVP reminders ---
                rsvps = db.get_reminders_due(event_id)
                for rsvp in rsvps:
                    reminder_minutes = rsvp["reminder_minutes"]
                    discord_id = rsvp.get("discord_id")
                    player_name = rsvp["player_name"]

                    self.logger.debug(f"[ReminderCheck] {player_name} → reminder: {reminder_minutes} | now: {mins_until}")

                    if abs(reminder_minutes - mins_until) <= 1:
                        if discord_id:
                            mention = f"<@{discord_id}>"
                        else:
                            mention = player_name

                        hours = round(reminder_minutes / 60, 1)
                        await channel.send(f"⏰ {mention} — *the* event starts in {hours} hours!")
                        db.clear_reminder(event_id, player_name)
                        self.logger.info(f"[ReminderSent] Sent to {player_name} for event {event_id} ({title})")

        except Exception as e:
            err.log_error("rmd.run_reminders", e, include_trace=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.start()

def setup(bot):
    bot.add_cog(ReminderCog(bot))
