import discord
from discord.ext import commands

# List to store disabled slash commands
disabled_slash_commands = []


class CommandManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="disable", description="Disable a slash command")
    async def disable(self, ctx, command_name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to run this command", ephemeral=True)
            return

        # Get list of slash commands from list_commands command in SlashCog
        slash_cog = ctx.bot.get_cog("SlashCog")
        if slash_cog:
            # Call list_commands as a method of the SlashCog instance
            slash_commands = await slash_cog.list_commands(ctx)

            if command_name in slash_commands:
                if command_name not in disabled_slash_commands:
                    disabled_slash_commands.append(command_name)
                    await ctx.send(f'{command_name} has been disabled.')
                else:
                    await ctx.send(f'{command_name} is already disabled.')
            else:
                await ctx.send(f'{command_name} is not a valid slash command.')
        else:
            await ctx.send("SlashCog not found.")

    @commands.command(name="enable", description="Enable a slash command")
    async def enable(self, ctx, command_name: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to run this command", ephemeral=True)
            return

        if command_name in disabled_slash_commands:
            disabled_slash_commands.remove(command_name)
            await ctx.send(f'{command_name} has been enabled.')
        else:
            await ctx.send(f'{command_name} is not disabled.')

    # Listener to check if the command is disabled
    @commands.Cog.listener()
    async def on_command(self, ctx):
        command_name = ctx.command.name.lower()
        cog_name = ctx.command.cog_name.lower() if ctx.command.cog_name else None
        if cog_name and cog_name in disabled_commands and command_name in disabled_commands[cog_name]:
            await ctx.send("This command is currently disabled.")
            raise commands.DisabledCommand


async def setup(bot):
    await bot.add_cog(CommandManagement(bot))
