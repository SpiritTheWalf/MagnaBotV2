import os
import discord
import log_cog
import moderation
import sheri
import slashcommands
import spiritonly

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()  # Sets the intents
intents.members = True  # Allows the bot to see the members in servers
intents.message_content = True  # Allows the bot to read messages in servers
TOKEN = os.getenv("BOT_TOKEN")
COMMAND_PREFIX = "?"  # Sets the bot's default command prefix
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


# Load cogs function
# Load cogs function
async def load_cogs(bot):
    cogs = [log_cog, moderation, slashcommands, sheri, spiritonly]
    for cog in cogs:
        if not bot.get_cog(cog.__name__):
            try:
                await bot.load_extension(cog.__name__)
                print(f"Cog {cog.__name__} loaded!")
            except Exception as e:
                print(f"Failed to load cog {cog.__name__}: {e}")
    print("Cogs loaded!")


# Bot ready event
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    for command in bot.commands:
        print(command.name)  # Prints all non app commands to the console
    print('Ready!')


@bot.command()
async def load(ctx):
    print('Load command executed!')
    await load_cogs()
    await ctx.send('Cogs loaded!')


# Command to set bot's presence, can only be done by SpiritTheWalf, or whoever is running the bot
@bot.command()
@commands.is_owner()
async def dotstatus(ctx: commands.Context, status: str):
    status = status.lower()
    presence_status = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.do_not_disturb,
        "offline": discord.Status.invisible
    }.get(status)
    if presence_status is None:
        await ctx.send("Invalid status. Please use one of the following: online, idle, dnd, offline")
        return
    await bot.change_presence(status=presence_status)
    await ctx.send(f"Bot presence status set to: {status.capitalize()}")


# Command to sync app command tree
@bot.command(pass_context=True)
@commands.is_owner()
async def sync(ctx):
    await ctx.bot.tree.sync()
    await ctx.send("Commands synced, you will need to reload Discord to see them")


@bot.command()
@commands.is_owner()
async def status(ctx, *, new_status: str):
    await bot.change_presence(activity=discord.Game(name=new_status))
    await ctx.send(f"Bot status changed to: {new_status}")
    await ctx.message.delete()


@bot.command()
@commands.is_owner()
async def nickname(ctx, *, new_nickname: str):
    for guild in bot.guilds:
        try:
            await guild.me.edit(nick=new_nickname)
            await ctx.send(f"Bot nickname changed to: {new_nickname} in {guild.name}")
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"Failed to change nickname in {guild.name}: {e}")


# Define a command to get the name and ID of every guild the bot is in
@bot.command()
@commands.is_owner()
async def glist(ctx):
    guilds = bot.guilds
    for guild in guilds:
        await ctx.send(f'Guild Name: {guild.name}, Guild ID: {guild.id}')


@bot.command()
@commands.is_owner()
async def ginfo(ctx, guild_id: int):
    guild = bot.get_guild(guild_id)
    if guild is not None:
        owner = guild.owner
        total_members = guild.member_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        created_at = guild.created_at.strftime('%Y-%m-%d %H:%M:%S')

        # Check if the bot is in the guild
        bot_member = guild.get_member(bot.user.id)
        if bot_member is not None:
            joined_at = bot_member.joined_at.strftime('%Y-%m-%d %H:%M:%S')
        else:
            joined_at = "Not found"

        embed = discord.Embed(title=f'Guild Information - {guild.name}', color=discord.Color.blue())
        embed.add_field(name='Owner', value=f'{owner.name}#{owner.discriminator}', inline=False)
        embed.add_field(name='Total Members', value=total_members, inline=False)
        embed.add_field(name='Text Channels', value=text_channels, inline=False)
        embed.add_field(name='Voice Channels', value=voice_channels, inline=False)
        embed.add_field(name='Created At', value=created_at, inline=False)
        embed.add_field(name='Bot Joined At', value=joined_at, inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("Guild not found.")


@bot.command()
@commands.is_owner()
async def rlist(ctx, guild_id: int):
    guild = bot.get_guild(guild_id)
    if guild is not None:
        roles = guild.roles
        roles_list = "\n".join([f'{role.name} - ID: {role.id}' for role in roles if role.name != '@everyone'])
        await ctx.send(f'Roles in {guild.name}:\n{roles_list}')
    else:
        await ctx.send("Guild not found.")


@bot.command()
@commands.is_owner()
async def rperms(ctx, role_id: int):
    role = discord.utils.get(ctx.guild.roles, id=role_id)
    if role is not None:
        permissions = role.permissions
        perms_list = '\n'.join([perm[0].replace('_', ' ').title() for perm in permissions if perm[1]])
        await ctx.send(f'Permissions for {role.name} - ID: {role.id}:\n{perms_list}')
    else:
        await ctx.send("Role not found.")

@bot.command()
@commands.has_permissions(kick_members=True, administrator=True)
async def senddm(ctx, user_id: int, *, message: str):
    user = bot.get_user(user_id)
    if user is not None:
        try:
            await user.send(message)
            await ctx.send("Done")
        except discord.HTTPException:
            await ctx.send(f'Failed to send a message to {user.name}#{user.discriminator}')
    else:
        await ctx.send("User not found.")


# Setup hook
@bot.event
async def on_connect():
    print("Bot is starting")
    await load_cogs(bot)
    print("Setup complete!")


bot.run(TOKEN)
