import discord
import sqlite3
from discord import app_commands
from discord.ext import commands
from datetime import datetime

DATABASE_FILE = "logging_cog.db"


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_connection(self):  # Connect to the database
        return sqlite3.connect(DATABASE_FILE)

    async def get_default_logging_channel(self, guild_id):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute(f"SELECT default_logging_channel FROM guilds WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            default_channel_id = result[0] if result else None
            print(f"Default logging channel for guild {guild_id}: {default_channel_id}")
            return default_channel_id
        except sqlite3.Error as e:
            print(f"Error retrieving default logging channel ID: {e}")
        finally:
            if conn:
                conn.close()

    async def send_warning_embeds(self, channel, guild, issuer, user,
                                  reason):  # This is the embed format for the /warn command
        warning_embed = discord.Embed(title="User Warned", color=discord.Color.orange())
        warning_embed.add_field(name="User", value=user.display_name, inline=False)
        warning_embed.set_thumbnail(url=user.avatar.url)
        warning_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
        warning_embed.add_field(name="Reason", value=reason, inline=False)
        warning_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                                inline=False)

        await channel.send(embed=warning_embed)

    async def send_kick_logging_embed(self, channel, guild, user, issuer, reason):
        embed = discord.Embed(title="User Kicked", color=discord.Color.red())
        embed.add_field(name="User", value=user.mention)
        embed.add_field(name="Issuer", value=issuer.mention)
        embed.add_field(name="Reason", value=reason)
        embed.set_footer(text=f"Guild: {guild.name} | Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        await channel.send(embed=embed)

    @app_commands.command(name="warn", description="Warn a user for violating rules")
    async def warn_command(self, inter: discord.Interaction, user: discord.Member, reason: str):
        guild = inter.guild
        if not guild:
            await inter.response.send_message("This command must be used in a server.")
            return

        # Check if the issuer has the "Kick Members" permission or is an administrator
        issuer = inter.user
        if not issuer.guild_permissions.kick_members and not issuer.guild_permissions.administrator:
            await inter.response.send_message("You don't have permission to use this command.")
            return

        # Get the default logging channel
        default_channel_id = await self.get_default_logging_channel(guild.id)
        if not default_channel_id:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Get the default logging channel
        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Send warning embed to default logging channel
        await self.send_warning_embeds(default_channel, guild, user, issuer, reason)

        # Direct message the user being warned
        try:
            warning_embed = discord.Embed(title="You have been warned!", color=discord.Color.orange())
            warning_embed.set_thumbnail(url=user.avatar.url)
            warning_embed.add_field(name="Server", value=guild.name, inline=False)
            warning_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
            warning_embed.add_field(name="Reason", value=reason, inline=False)
            warning_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    inline=False)

            await user.send(embed=warning_embed)
        except discord.Forbidden:
            await inter.response.send_message("Failed to DM the user. Make sure they have DMs enabled.", ephemeral=True)

        await inter.response.send_message("User has been warned successfully.", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a user from the server")
    async def kick_command(self, inter: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        guild = inter.guild
        issuer = inter.user

        # Check if the issuer has the "Kick Members" permission or is an administrator
        if not issuer.guild_permissions.kick_members and not issuer.guild_permissions.administrator:
            await inter.response.send_message("You don't have permission to use this command.")
            return

        # Send DM to the kicked user
        try:
            kick_dm_embed = discord.Embed(title="You have been kicked from the server!", color=discord.Color.red())
            kick_dm_embed.set_thumbnail(url=user.avatar.url)
            kick_dm_embed.add_field(name="Server", value=guild.name, inline=False)
            kick_dm_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
            kick_dm_embed.add_field(name="Reason", value=reason, inline=False)
            kick_dm_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    inline=False)

            await user.send(embed=kick_dm_embed)
        except discord.Forbidden:
            await inter.response.send_message(
                "Failed to send a DM to the kicked user. Make sure they have DMs enabled.")

        # Kick the user
        try:
            await user.kick(reason=reason)
        except discord.Forbidden:
            await inter.response.send_message("I don't have permission to kick that user.")
            return

        # Get the default logging channel
        default_channel_id = await self.get_default_logging_channel(guild.id)
        if not default_channel_id:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Get the default logging channel
        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Send kick embed to default logging channel
        try:
            await self.send_kick_logging_embed(default_channel, guild, user, issuer, reason)
            await inter.response.send_message(f"{user.mention} has been kicked from the server for: {reason}",
                                              ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Failed to send embed to the default logging channel: {e}",
                                              ephemeral=True)

    async def send_ban_embed(self, channel, user, issuer, reason):  # Defines the structure of the embed
        ban_embed = discord.Embed(title="User Banned", color=discord.Color.red())
        ban_embed.set_thumbnail(url=user.avatar.url)
        ban_embed.add_field(name="User", value=user.display_name, inline=False)
        ban_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
        ban_embed.add_field(name="Reason", value=reason, inline=False)
        ban_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            inline=False)
        await channel.send(embed=ban_embed)

    @app_commands.command(name="ban", description="Ban a user from the server")
    async def ban_command(self, inter: discord.Interaction, user_id: str = None, username: str = None,
                          reason: str = "No reason provided"):
        issuer = inter.user
        guild = inter.guild

        # Check if the issuer has the "Ban Members" permission or is an administrator
        if not issuer.guild_permissions.ban_members and not issuer.guild_permissions.administrator:
            await inter.response.send_message("You don't have permission to use this command.")
            return

        # Ensure only one of user_id or username is provided
        if (user_id is None and username is None) or (user_id is not None and username is not None):
            await inter.response.send_message("Please provide either a user ID or a username, not both.")
            return

        # Convert user_id from string to integer if it's a numeric string
        if user_id is not None and user_id.isdigit():
            user_id = int(user_id)

        # Fetch the member object using user ID or username
        user = None
        if user_id is not None:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                await inter.response.send_message("User not found.")
                return
        elif username is not None:
            user = discord.utils.get(guild.members, name=username)
            if user is None:
                await inter.response.send_message("User not found.")
                return

        # Send DM to the user
        try:
            ban_dm_embed = discord.Embed(title="You have been banned from the server!", color=discord.Color.red())
            ban_dm_embed.set_thumbnail(url=user.avatar.url)
            ban_dm_embed.add_field(name="Server", value=guild.name, inline=False)
            ban_dm_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
            ban_dm_embed.add_field(name="Reason", value=reason, inline=False)
            ban_dm_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                   inline=False)
            await user.send(embed=ban_dm_embed)
        except discord.Forbidden:
            await inter.response.send_message("Failed to send a DM to the user. Make sure they have DMs enabled.")

        # Ban the user
        try:
            await guild.ban(user, reason=reason)
        except discord.Forbidden:
            await inter.response.send_message("I don't have permission to ban that user.")
            return

        # Get the default logging channel
        default_channel_id = await self.get_default_logging_channel(guild.id)
        if not default_channel_id:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Get the default logging channel
        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Send ban embed to default logging channel
        await self.send_ban_embed(default_channel, user, issuer, reason)

        await inter.response.send_message(f"{user.mention} has been banned from the server for: {reason}")

    async def send_unban_embed(self, channel, user, issuer):  # Defines the embed for the unban command
        unban_embed = discord.Embed(title="User Unbanned", color=discord.Color.green())
        unban_embed.set_thumbnail(url=user.avatar.url)
        unban_embed.add_field(name="User", value=user.display_name, inline=False)
        unban_embed.add_field(name="Issuer", value=issuer.display_name, inline=False)
        unban_embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                              inline=False)
        await channel.send(embed=unban_embed)

    @app_commands.command(name="unban", description="Unban a user from the server")
    async def unban_command(self, inter: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        issuer = inter.user
        guild = inter.guild

        # Check if the issuer has the "Ban Members" permission or is an administrator
        if not issuer.guild_permissions.ban_members and not issuer.guild_permissions.administrator:
            await inter.response.send_message("You don't have permission to use this command.")
            return

        # Convert user_id to integer
        try:
            user_id = int(user_id)
        except ValueError:
            await inter.response.send_message("Invalid user ID provided.")
            return

        # Convert user_id to discord.User object
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            await inter.response.send_message("User not found.")
            return

        # Unban the user
        try:
            await guild.unban(user, reason=reason)
        except discord.Forbidden:
            await inter.response.send_message("I don't have permission to unban that user.")
            return

        # Get the default logging channel
        default_channel_id = await self.get_default_logging_channel(guild.id)
        if not default_channel_id:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Get the default logging channel
        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            await inter.response.send_message("Default logging channel not found.")
            return

        # Send unban embed to default logging channel
        await self.send_unban_embed(default_channel, user, issuer)

        await inter.response.send_message(f"{user.mention} has been unbanned from the server.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
    print("ModerationCog loaded successfully!")
