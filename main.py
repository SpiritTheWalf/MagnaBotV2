import os
import discord
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
async def load_cogs(bot):
    cogs = []  # Add cogs to be loaded here
    for cog in cogs:
        if not bot.get_cog(cog.__name__):
            try:
                await bot.load_extention(cog.__name__)
                print(f"Cog {cog.__name__} loaded!")
            except Exception as e:
                print(f"Failed to load cog {cog.__name__}: {e:}")
    print("Cogs loaded!")


# Bot ready event
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    for command in bot.commands:
        print(command.name)  # Prints all non app commands to the console
    members = sum(guild.member_count - 1 for guild in
                  bot.guilds)  # Counts all members in all guilds and sets that as the bot's status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{members} members"
    ))
    print("Bot ready!")


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


# Setup hook
@bot.event
async def on_connect():
    print("Bot is starting")
    await load_cogs(bot)
    print("Setup complete!")


bot.run(TOKEN)
