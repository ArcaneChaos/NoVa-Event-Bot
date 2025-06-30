# .env file for NovaBot

# Discord Bot Token (REQUIRED)
# Get this from your Discord Developer Portal -> Applications -> Your Bot -> Bot -> Token
DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE"

# Role ID for AdministrativePermissions (REQUIRED if using auth.py)
# This is the ID of the Discord role that will grant special permissions (e.g., creating events, deleting players).
# You can get a role ID by enabling Developer Mode in Discord (User Settings -> Advanced -> Developer Mode),
# then right-clicking the role in your server's Role settings and selecting "Copy ID".
EXAMPLE_ROLE_ID=1234567890123456789 # Replace with your actual role ID

# Channel ID for Reminders and Event Notifications (REQUIRED if using rmd.py, crev.py, evt_mod.py)
# This is the ID of the Discord channel where the bot will send event notifications and reminders.
# Get this by right-clicking the channel in Discord and selecting "Copy ID" in dev mode.
REMINDER_CHANNEL_ID=9876543210987654321 # Replace with your actual channel ID

# Channel ID for the Dashboard Message (REQUIRED if using clean.py and sending dashboard messages)
# HARDCODED IN clean.py MAKE SURE YOU UPDATE
DASHBOARD_CHANNEL_ID=5678901234567890123 # Replace with your actual channel ID
