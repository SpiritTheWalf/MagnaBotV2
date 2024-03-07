import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

DATABASE_FILE = "logging_cog.db"


class LoggingCog(commands.Cog):  # Defines our LoggingCog
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_connection(self):  # Connects to the logging database
        return sqlite3.connect(DATABASE_FILE)

    def load_default_logging_channel(self, guild_id):  # Loads the default logging channel from the database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT default_logging_channel FROM guilds WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            logging_channel_id = result[0] if result else None
            if logging_channel_id:
                print(f"Loaded default logging channel ID {logging_channel_id} for guild {guild_id}")
            else:
                print(f"No default logging channel found for guild {guild_id}")
            return logging_channel_id

    def save_default_logging_channel(self, guild_id, channel_id):  # Saves the default logging channel to the database
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("REPLACE INTO guilds (guild_id, default_logging_channel) VALUES(?, ?)",
                           (guild_id, channel_id))
            conn.commit()
            print(f"Saved default logging channel ID {channel_id} for guild {guild_id}")

    @app_commands.command(name="defaultloggingchannel", description="Prints the default logging channel for the server")
    async def default_logging_channel(self, inter: discord.Interaction):
        guild = inter.guild
        channel_id = self.load_default_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel:
                await inter.response.send_message(f"The default logging channel for this server is: {channel.mention}",
                                                  ephemeral=True)
            else:
                await inter.response.send_message("The default logging channel is not set in this server, you can set "
                                                  "it by running `/setloggingchannel <channel>`", ephemeral=True)
        else:
            await inter.response.send_message("The default logging channel is not set in this server, you can set "
                                              "it by running `/setloggingchannel <channel>`", ephemeral=True)

    @app_commands.command(name="setloggingchannel", description="Sets the default logging channel for the server")
    async def set_logging_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        guild = inter.guild
        if not inter.user.guild_permissions.administrator:
            await inter.response.send_message("You do not have permission to run this command", ephemeral=True)
            return

        self.save_default_logging_channel(guild.id, channel.id)
        await inter.response.send_message(f"Default logging channel set to {channel.mention}", ephemeral=True)

    async def send_join_leave_logging_embed(self, guild, action, member):  # Sends an embed to the default logging
        # channel whenever someone joins or leaves the server
        channel_id = self.load_default_logging_channel(guild.id)
        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title=f"Member {action}",
                    color=discord.Color.green() if action == 'joined' else discord.Color.red()
                )
                embed.set_thumbnail(url=member.avatar.url)
                embed.add_field(name="User", value=member.mention, inline=False)
                embed.add_field(name="User ID", value=member.id, inline=False)
                embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()  # Listens for a member joining the server, then fires the send_join_leave_logging_embed
    # function
    async def on_member_join(self, member):
        guild = member.guild
        await self.send_join_leave_logging_embed(guild, "joined", member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        cutoff_time = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(
            seconds=30)  # Adjust the time frame as needed

        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick):
            if entry.target == member and entry.created_at > cutoff_time:
                await self.send_join_leave_logging_embed(guild, "kicked", member)
                return

        await self.send_join_leave_logging_embed(guild, "left", member)

    async def send_message_edit_logging_embed(self, before, after):  # Sends an embed whenever a message is edited
        channel_id = self.load_default_logging_channel(after.guild.id)
        if channel_id:
            channel = after.guild.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title="Message Edited",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Original Message", value=before.content, inline=False)
                embed.add_field(name="Edited Message", value=after.content, inline=False)
                embed.add_field(name="Author", value=before.author.mention, inline=False)
                embed.add_field(name="Channel", value=after.channel.mention, inline=False)
                embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                inline=False)
                await channel.send(embed=embed)

    @commands.Cog.listener()  # Listens for an edited message, then fires the send_message_edit_logging_embed function
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        await self.send_message_edit_logging_embed(before, after)

    async def send_reaction_logging_embed(self, guild, action, target, user):  # Sends an embed to the default
        # logging channel whenever a reaction is added to or removed from a message
        default_channel_id = self.load_default_logging_channel(guild.id)
        if not default_channel_id:
            return

        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            return

        embed = discord.Embed(title=f"Reaction {action}",
                              color=discord.Color.green() if action == 'added' else discord.Color.red())
        embed.set_thumbnail(url=target.guild.icon.url)
        embed.add_field(name="Message Author", value=target.author.mention, inline=False)
        embed.add_field(name="Message Content", value=target.content, inline=False)
        embed.add_field(name="Reaction Author", value=user.mention, inline=False)
        embed.add_field(name="Emoji", value=str(reaction.emoji), inline=False)
        embed.add_field(name="Channel", value=target.channel.mention, inline=False)
        embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

        await default_channel.send(embed=embed)

    @commands.Cog.listener()  # Listens for a reaction added to a message
    async def on_raw_reaction_add(self, payload):
        if before.author.bot:
            return
        await self.log_reaction_event(payload, "added")

    @commands.Cog.listener()  # Listens for a reaction removed from a message
    async def on_raw_reaction_remove(self, payload):
        if before.author.bot:
            return
        await self.log_reaction_event(payload, "removed")

    async def log_reaction_event(self, payload, action):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        user = guild.get_member(payload.user_id)
        if not user:
            return

        emoji = payload.emoji

        default_channel_id = self.load_default_logging_channel(guild.id)
        if not default_channel_id:
            return

        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            return

        embed = discord.Embed(
            title=f"Reaction {action}",
            description=f"Emoji: {emoji}",
            color=discord.Color.green() if action == "added" else discord.Color.red()
        )
        embed.add_field(name="User", value=user.mention, inline=False)
        embed.add_field(name="Message", value=message.content, inline=False)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

        try:
            await default_channel.send(embed=embed)
        except Exception as e:
            print(f"Error occurred while sending reaction event embed: {e}")

    @commands.Cog.listener()  # Listens for a member joining or leaving a voice channel
    async def on_voice_state_update(self, member, before, after):
        if before.author.bot:
            return
        guild = member.guild

        # Check if the user joined or left a voice channel
        if before.channel != after.channel:
            action = "joined" if after.channel else "left"
            voice_channel = after.channel if after.channel else before.channel

            default_channel_id = self.load_default_logging_channel(guild.id)
            if default_channel_id:
                default_channel = guild.get_channel(default_channel_id)
                if default_channel:
                    try:
                        embed = discord.Embed(
                            title=f"Voice {action.capitalize()}",
                            color=discord.Color.green() if action == "joined" else discord.Color.red()
                        )
                        embed.add_field(name="User", value=member.mention, inline=False)
                        embed.add_field(name="Voice Channel", value=voice_channel.mention, inline=False)
                        embed.add_field(name="Timestamp", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                        inline=False)

                        await default_channel.send(embed=embed)
                    except Exception as e:
                        print(f"Error occurred while sending voice event embed: {e}")
                else:
                    print("Default logging channel not found.")
            else:
                print("Default logging channel ID not found.")

    async def send_message_deleted_embed(self, channel, message):
        if not message.author:  # Check if the message has a valid author
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

    @commands.Cog.listener()  # Listens for deleted messages and fires the embed when one is detected
    async def on_message_delete(self, message):
        if before.author.bot:
            return
        guild = message.guild

        default_channel_id = self.load_default_logging_channel(guild.id)
        if not default_channel_id:
            return

        default_channel = guild.get_channel(default_channel_id)
        if not default_channel:
            return

        # Check if the message is not from the bot itself
        if message.author != self.bot.user:
            # Send message deleted embed to default logging channel
            await self.send_message_deleted_embed(default_channel, message)


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingCog(bot))
