import os
import discord
import requests
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

load_dotenv()
API_KEY = os.getenv("SHERI_API_KEY")


class SheriCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://sheri.bot/api/list_all"
        self.api_key = API_KEY  # Replace this with your actual API key

    @commands.command()
    async def list_cogs(self, ctx):
        loaded_cogs = '\n'.join(self.bot.cogs.keys())
        await ctx.send(f"Loaded cogs: \n{loaded_cogs}")

    @commands.command()
    async def endpoints(self, ctx):
        if ctx.channel.is_nsfw():
            await ctx.send(
                "# SFW ENDPOINTS\n\nbday, belly_rub, blep, bonk, boop, bunny, cat, cry, cuddle, deer, fox, "
                "goat, hold, horse, hug, husky, kiss, lick, lion, mur, nature, pat, paws, pig, plane, "
                "pokemon, proposal, rpanda, sfwsergal, shiba, snek, snep, tiger, turkey, turtle, wolves, "
                "yeen\n\n\n\n# NSFW ENDPOINTS\n\n69, anal, bang, bisexual, boob, boobwank, "
                "boop, booty, christmas, cumflation, cuntboy, cuntboy_bang, deer, "
                "dick, dick_wank, dickmilk, dickorgy, dp, fbound, fcreampie, femboypresentation, finger, "
                "fpresentation, frot, fseduce, fsolo, ftease, futabang, gay, gay_bang, gif, "
                "handjob, herm_bang, impregnated, jockstraps, lesbian, "
                "lesbian_bang, lick, maws, mbound, mcreampie, mpresentation, mseduce, msolo, mtease, "
                "nboop, nbrony, nbulge, ncomics, ncuddle, ndeer, nfelkins, nfemboy, nfox, "
                "nfuta, ngroup, nhold, nhug, nhusky, nkiss, nleopard, nlick, npanther, npat, npokemon, "
                "nprotogen, nscalies, nsfwselfies, nsolo, nspank, ntease, ntrap, pawjob, pawlick, "
                "paws, pegging_bang, petplay, pregnant, pussy, "
                "pussy_eating, ride, rimjob, rpanda, selfsuck, sfwsergal, "
                "straight_bang, suck, tentacles, toys, videos, vore, vorefanal, "
                "voreforal, vorefunbirth, voremanal, voremcock, voremoral, wolves, yiff"
            )

        else:
            await ctx.send("SFW ENDPOINTS\n\nbday, belly_rub, blep, bonk, boop, bunny, cat, cry, cuddle, deer, fox, "
                           "goat, hold, horse, hug, husky, kiss, lick, lion, mur, nature, pat, paws, pig, plane, "
                           "pokemon, proposal, rpanda, sfwsergal, shiba, snek, snep, tiger, turkey, turtle, wolves, "
                           "yeen")

    @app_commands.command(name="media", description="Pulls an image from a specified endpoint")
    async def media(self, inter: discord.Interaction, endpoint: str = None):
        """
        Pulls an image from a specified endpoint.
        """
        try:
            # Define the list of valid endpoints for SFW and NSFW channels
            sfw_endpoints = ["bday", "belly_rub", "blep", "bonk", "boop", "bunny", "cat", "cry", "cuddle", "deer",
                             "fox",
                             "goat", "hold", "horse", "hug", "husky", "kiss", "lick", "lion", "mur", "nature",
                             "pat", "paws",
                             "pig", "plane", "pokemon", "proposal", "rpanda", "sfwsergal", "shiba", "snek",
                             "snep", "tiger",
                             "turkey", "turtle", "wolves", "yeen"]
            nsfw_endpoints = ["69", "anal", "bang", "bisexual", "boob",
                              "boobwank",
                              "booty", "christmas", "cumflation", "cuntboy", "cuntboy_bang","dick",
                              "dick_wank",
                              "dickmilk", "dickorgy", "dp", "fbound", "fcreampie", "femboypresentation", "finger",
                              "fpresentation",
                              "frot", "fseduce", "fsolo", "ftease", "futabang", "gay", "gay_bang", "gif",
                              "handjob", "herm_bang",
                              "impregnated", "jockstraps", "lesbian", "lesbian_bang", "maws", "mbound",
                              "mcreampie", "mpresentation",
                              "mseduce", "msolo", "mtease", "nboop", "nbrony", "nbulge", "ncomics", "ncuddle",
                              "ndeer", "nfelkins",
                              "nfemboy", "nfox", "nfuta", "ngroup", "nhold", "nhug", "nhusky", "nkiss",
                              "nleopard", "nlick", "npanther",
                              "npat", "npokemon", "nprotogen", "nscalies", "nsfwselfies", "nsolo", "nspank",
                              "ntease", "ntrap", "pawjob",
                              "pawlick", "paws", "pegging_bang", "petplay", "pregnant", "pussy", "pussy_eating",
                              "ride", "rimjob", "rpanda", "selfsuck", "straight_bang", "suck",
                              "tentacles", "toys", "videos", "vore", "voreforal", "vorefunbirth", "voremanal",
                              "voremcock", "voremoral", "yiff"]

            all_endpoints = sfw_endpoints + nsfw_endpoints

            # Check if the endpoint is provided
            if endpoint is None:
                await inter.response.defer()
                options = [discord.SelectOption(label=e, value=e) for e in all_endpoints]
                await inter.response.send_message("Please select an endpoint:", components=[discord.ActionRow(
                    discord.Select(options=options, custom_id="endpoint_selection"))])
                return

            if endpoint not in all_endpoints:
                await inter.response.send_message("Invalid endpoint, please run `?endpoints` to see all available "
                                                  "endpoints.")
                return

            # Check if the endpoint is NSFW and if NSFW content is allowed in the channel
            if endpoint in nsfw_endpoints and not inter.channel.is_nsfw():
                await inter.response.send_message("This endpoint is NSFW and can only be used in NSFW channels.")
                return

            # Proceed with fetching the image using the provided endpoint...
            api_url = f"https://sheri.bot/api/{endpoint}"
            headers = {
                "Authorization": f"Token {self.api_key}",
                "User-Agent": "MagnaBot/1.0 (Python Requests)"
            }
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                # Extract the image URL from the JSON response
                image_url = response.json().get('url')
                if image_url:
                    embed = discord.Embed()
                    embed.set_image(url=image_url)
                    await inter.response.send_message(embed=embed)
                else:
                    await inter.response.send_message("Error: No image URL found in the response.")
            else:
                await inter.response.send_message(
                    f"Error: Could not fetch image from {api_url}. Status code: {response.status_code}")
        except Exception as e:
            await inter.response.send_message(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(SheriCog(bot))
