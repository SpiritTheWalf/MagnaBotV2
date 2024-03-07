import discord
from datetime import datetime
from pytz import all_timezones, timezone
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)


class SlashCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready!")

    @app_commands.command(name="support", description="Prints an invite to the support server")
    async def support(self, inter: discord.Interaction):
        await inter.response.send_message("The main support server:https://discord.gg/bYEYvA7R3G\n The beta support "
                                          "server:https://discord.com/invite/shgUJqmJhW")

    @app_commands.command(name="list_commands", description="List all commands for the bot")
    async def list_commands(self, inter: discord.Interaction):
        normal_commands = [command.name for command in self.bot.commands]
        slash_commands = []

        # Iterate over attributes of the class to find slash commands
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, app_commands.Command):
                slash_commands.append(attr.name)

        response = f"**Normal Commands:**\n{', '.join(normal_commands)}\n\n"
        response += f"**Slash Commands:**\n{', '.join(slash_commands)}"

        await inter.response.send_message(content=response)

    @app_commands.command(name="timenow", description="What is the time in a particular time zone?")
    async def timenow(self, inter: discord.Interaction, timezone_name: str, ):
        fmt = "%Y-%m-%d %H:%M:%S %Z%z"

        if timezone_name not in all_timezones:
            await inter.response.send_message("Unknown timezone. Please provide a valid timezone name.")
            return

        now_utc = datetime.now(timezone('UTC'))
        selected_timezone = timezone(timezone_name)
        selected_time = now_utc.astimezone(selected_timezone)

        await inter.response.send_message(selected_time.strftime(fmt) + f" ({timezone_name})")

    @app_commands.command(name="tzlist", description="Prints all available timezones")
    async def tzlist(self, inter: discord.Interaction):
        await inter.response.send_message(
            "The valid timezones are:\n Europe/London\n Europe/Berlin\n CET\n Israel\n Canada/Eastern\n US/Central\n "
            "US/Pacific")

    @app_commands.command(
        name="roleadd",
        description="Adds a role to a user"
    )
    async def roleadd(self, inter: discord.Interaction, user: discord.Member, role: discord.Role):
        if inter.user.guild_permissions.manage_roles or inter.user.guild_permissions.administrator:
            await user.add_roles(role)
            await inter.response.send_message(f"Added role {role.name} to {user.display_name}")
        else:
            await inter.response.send_message("You do not have permission to manage roles.")

    @app_commands.command(
        name="roleremove",
        description="Removes a role from a user"
    )
    async def roleremove(self, inter: discord.Interaction, user: discord.Member, role: discord.Role):
        if inter.user.guild_permissions.manage_roles or inter.user.guild_permissions.administrator:
            await user.remove_roles(role)
            await inter.response.send_message(f"Removed role {role.name} from {user.display_name}")
        else:
            await inter.response.send_message("You do not have permission to manage roles.")

    @app_commands.command(
        name="rolequery",
        description="Check if a user has a particular role"
    )
    async def rolequery(self, inter: discord.Interaction, user: discord.Member, role: discord.Role):
        if role in user.roles:
            await inter.response.send_message(f"{user.display_name} has the role {role.name}.")
        else:
            await inter.response.send_message(f"{user.display_name} does not have the role {role.name}.")

    @app_commands.command(
        name="getuserroles",
        description="List all roles a user has"
    )
    async def getuserroles(self, inter: discord.Interaction, user: discord.Member):
        role_list = ", ".join([role.name for role in user.roles])
        await inter.response.send_message(f"{user.display_name} has the following roles: {role_list}")

    async def setup(self):
        pass  # Add initialization code if needed

async def setup(bot: commands.Bot):
    for cog in bot.cogs.values():
        if isinstance(cog, SlashCog):
            print("'SlashCog' cog is already loaded.")
            return
    cog = SlashCog(bot)
    await cog.setup()
    await bot.add_cog(cog)
