import os
import discord
from utils import err

EXAMPLE_ROLE_ID = int(os.getenv("EXAMPLE_ROLE_ID", 0))

async def is_r4(interaction: discord.Interaction) -> bool:
    """Check if user has R4 role. Falls back to fetch if roles missing."""
    try:
        user = interaction.user
        # If roles are missing (not cached), fetch fresh
        if not hasattr(user, "roles"):
            user = await interaction.guild.fetch_member(user.id)

        return any(role.id == EXAMPLE_ROLE_ID for role in user.roles)

    except Exception as e:
        err.log_error("auth.is_r4", e)
        return False

async def require_r4(interaction: discord.Interaction) -> bool:
    """Send message and return False if user lacks R4 role."""
    if not await is_r4(interaction):
        try:
            await interaction.response.send_message(
                err.user_error("You must be R4 or Admin to do this."),
                ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                err.user_error("You must be R4 or Admin to do this."),
                ephemeral=True
            )
        return False
    return True
