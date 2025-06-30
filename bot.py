import os
import logging
import discord
from dotenv import load_dotenv

# Load env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EXAMPLE_ROLE_ID = int(os.getenv("EXAMPLE_ROLE_ID", "0")) #you will need to name your own role or keep this one
LOG_PATH = "logs/bot.log"

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("nova")
logger.info("🔵 Bot starting...")

# Intents and bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)
bot.logger = logger
bot.r4_role_id = R4_ROLE_ID

# Load cogs
COGS = [
    "cogs.dash",
    "cogs.rmd",
    "cogs.clean",
]

for cog in COGS:
    try:
        bot.load_extension(cog)
        logger.info(f"✅ Loaded cog: {cog}")
    except Exception as e:
        logger.error(f"❌ Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")
    print(f"✅ Logged in as {bot.user}")
    synced = await bot.sync_commands()
    print(f"✅Synced slash commands")

bot.run(TOKEN)
