import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

DATABASE_FILE = "logging_cog.db"


class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_connection(self):
        return sqlite3.connect(DATABASE_FILE)

    def load_default_logging_channel(self, guild_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT default_logging_channel FROM guilds WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def save_default_logging_channel(self, guild_id, channel_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("REPLACE INTO guilds (guild_id, default_logging_channel) VALUES(?, ?)",
                           (guild_id, channel_id))
            conn.commit()

    @app_commands.command(name="defaultloggingchannel", description="Prints the default logging channel for the server")
    async def default_logging_channel(self, inter: discord.Interaction):
        guild = inter.guild
        channel_id = self.load_default_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await inter.response.send_message(f"The default logging channel for this server is: {channel.mention}",
                                                  ephemeral=True)
            else:
                await inter.response.send_message("The default logging channel is not set in this server.",
                                                  ephemeral=True)
        else:
            await inter.response.send_message("The default logging channel is not set in this server.",
                                              ephemeral=True)

    @app_commands.command(name="setloggingchannel", description="Sets the default logging channel for the server")
    async def set_logging_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        guild = inter.guild
        if not inter.user.guild_permissions.administrator:
            await inter.response.send_message("You do not have permission to run this command", ephemeral=True)
            return

        self.save_default_logging_channel(guild.id, channel.id)
        await inter.response.send_message(f"Default logging channel set to {channel.mention}", ephemeral=True)

    async def send_join_leave_logging_embed(self, guild, action, member, reason=None):
        channel_id = self.load_default_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"Member {action}",
                    color=discord.Color.green() if action == 'joined' else discord.Color.red()
                )
            if member.avatar:
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)
            else:
                embed.set_author(name=member.display_name)
                embed.add_field(name="User", value=member.mention, inline=False)
                embed.add_field(name="User ID", value=member.id, inline=False)
                if action == 'joined':
                    invites = await guild.invites()
                    invite_used = None
                    for invite in invites:
                        if invite.uses < invite.max_uses or invite.max_uses == 0:
                            invite_used = invite
                            break
                    invite_link = f"Used Invite: {invite_used.url}" if invite_used else "Unknown"
                    embed.add_field(name="Join Link", value=invite_link, inline=False)
                    embed.add_field(name="Account Creation Date",
                                    value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
                    embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    inline=False)
                if reason:
                    embed.add_field(name="Reason", value=reason.capitalize(), inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        channel_id = self.load_default_logging_channel(before.guild.id)
        if channel_id:
            channel = before.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Message Edited",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Before", value=before.content, inline=False)
                embed.add_field(name="After", value=after.content, inline=False)
                embed.add_field(name="Author", value=before.author.mention, inline=False)
                embed.add_field(name="Channel", value=before.channel.mention, inline=False)
                embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        reason = None

        cutoff_time = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(seconds=30)

        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick):
            if entry.target == member and entry.created_at > cutoff_time:
                reason = "kicked"
                break

        await self.send_join_leave_logging_embed(guild, "left", member, reason)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        await self.send_join_leave_logging_embed(guild, "joined", member)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        default_channel_id = self.load_default_logging_channel(guild.id)
        if default_channel_id:
            default_channel = guild.get_channel(default_channel_id)
            if default_channel:
                embed = discord.Embed(
                    color=discord.Color.blurple()
                )
                embed.add_field(name="User", value=member.mention, inline=False)

                # Add user's display name and profile picture
                embed.set_author(name=member.display_name, icon_url=member.avatar.url)

                # Check if the user joined a voice channel
                if before.channel is None and after.channel is not None:
                    embed.title = "Voice Channel Joined"
                    embed.add_field(name="Channel", value=after.channel.mention, inline=False)
                    embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    inline=False)
                    await default_channel.send(embed=embed)

                # Check if the user left a voice channel
                elif before.channel is not None and after.channel is None:
                    embed.title = "Voice Channel Left"
                    embed.add_field(name="Channel", value=before.channel.mention, inline=False)
                    embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                    inline=False)
                    await default_channel.send(embed=embed)

    async def send_message_deleted_embed(self, channel, message):
        if not message.author:
            return

        embed = discord.Embed(
            title="Message Deleted",
            color=discord.Color.red()
        )
        embed.add_field(name="Author", value=message.author.mention, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content, inline=False)
        embed.add_field(name="Timestamp", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        guild = message.guild
        default_channel_id = self.load_default_logging_channel(guild.id)
        if default_channel_id:
            default_channel = guild.get_channel(default_channel_id)
            if default_channel:
                await self.send_message_deleted_embed(default_channel, message)


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingCog(bot))
