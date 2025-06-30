import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils import db, err
import os

LOG_DIR = "logs"
LOG_RETENTION_DAYS = 5
REMINDER_RETENTION_MINUTES = 10
DASHBOARD_CHANNEL_ID =   #Replace with your actual dashboard channel ID

class CleanupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._loop_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._loop_started:
            self.cleanup_expired_data.start()
            self._loop_started = True

    @tasks.loop(minutes=10)
    async def cleanup_expired_data(self):
        try:
            now_dt = datetime.utcnow()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M")

            # 🧹 Expired event and RSVP cleanup
            deleted = db.delete_expired_events(now_str)
            if deleted > 0:
                self.bot.logger.info(f"🧹 Cleaned {deleted} expired events + orphaned RSVPs.")

            # 🧼 Clean expired dashboard messages
            channel = self.bot.get_channel(DASHBOARD_CHANNEL_ID)
            if channel:
                async for msg in channel.history(limit=50):
                    if msg.author == self.bot.user and any(keyword in msg.content for keyword in ["NoVa", "RSVP", "Your Time", "UTC:"]):
                        try:
                            await msg.delete()
                            self.bot.logger.info(f"🧹 Deleted stale dashboard: {msg.id}")
                        except Exception:
                            pass

            # ⏰ Clean stale reminders (if using per-event jobs)
            past_cutoff = now_dt - timedelta(minutes=REMINDER_RETENTION_MINUTES)
            past_events = [
                e for e in db.get_all_events()
                if datetime.strptime(e["datetime_utc"], "%Y-%m-%d %H:%M") < past_cutoff
            ]
            if hasattr(self.bot, "scheduler"):
                for evt in past_events:
                    job_id = f"reminder_{evt['id']}"
                    jobs = self.bot.scheduler.get_jobs()
                    if any(job.id == job_id for job in jobs):
                        self.bot.scheduler.remove_job(job_id)
                        self.bot.logger.info(f"⏳ Cancelled stale reminder job for event {evt['id']}")

            # 🗑️ Delete old log files
            cutoff = datetime.utcnow() - timedelta(days=LOG_RETENTION_DAYS)
            if os.path.isdir(LOG_DIR):
                for fname in os.listdir(LOG_DIR):
                    path = os.path.join(LOG_DIR, fname)
                    if os.path.isfile(path):
                        mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
                        if mtime < cutoff:
                            os.remove(path)
                            self.bot.logger.info(f"🧾 Deleted old log: {fname}")

        except Exception as e:
            err.log_error("clean.loop", e, include_trace=True)

def setup(bot):
    bot.add_cog(CleanupCog(bot))
