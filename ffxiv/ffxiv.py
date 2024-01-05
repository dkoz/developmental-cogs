import discord
from redbot.core import commands, Config, checks
import aiohttp
import asyncio

class Lodestone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://xivapi.com"
        self.config = Config.get_conf(self, identifier=9087263451)
        default_global = {
            "api_key": None
        }
        self.config.register_global(**default_global)
        default_user = {
            "server": None,
            "character_name": None
        }
        self.config.register_user(**default_user)

    @commands.command()
    @commands.is_owner()
    async def setapikey(self, ctx, *, key: str):
        """Set the API key for the FFXIV Lodestone."""
        await self.config.api_key.set(key)
        await ctx.send("API key set successfully.")

    async def get_api_key(self):
        """Retrieve the API key from the config."""
        return await self.config.api_key()

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def char(self, ctx, server_name: str, *, character_name: str):
        """Search for a character in the FFXIV database based on server and character name."""
        api_key = await self.get_api_key()
        url = f"{self.base_url}/character/search?name={character_name}&server={server_name}&private_key={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if 'Results' in data and data['Results']:
            character = data['Results'][0]
            character_id = character['ID']

            detailed_url = f"{self.base_url}/character/{character_id}?extended=1&private_key={api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(detailed_url) as detailed_response:
                    detailed_data = await detailed_response.json()

            char = detailed_data['Character']
            char_name = char['Name']
            char_server = char['Server']
            char_avatar = char['Avatar']
            char_portrait = char['Portrait']
            char_bio = char['Bio']
            char_race = char['Race']['Name']
            char_gender = "Male" if char['Gender'] == 1 else "Female"
            char_nameday = char['Nameday']
            char_guardian = char['GuardianDeity']['Name']
            char_active_class = f"{char['ActiveClassJob']['UnlockedState']['Name']} (Level {char['ActiveClassJob']['Level']})"

            embed = discord.Embed(
                title=char_name,
                description=char_server,
                url=f"https://na.finalfantasyxiv.com/lodestone/character/{character_id}/"
            )
            embed.set_thumbnail(url=char_avatar)
            embed.set_image(url=char_portrait)
            embed.add_field(name="Bio", value=char_bio, inline=False)
            embed.add_field(name="Race", value=char_race, inline=True)
            embed.add_field(name="Gender", value=char_gender, inline=True)
            embed.add_field(name="Nameday", value=char_nameday, inline=True)
            embed.add_field(name="Guardian Deity", value=char_guardian, inline=True)
            embed.add_field(name="Active Class/Job", value=char_active_class, inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("Character not found.")
            
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def csearch(self, ctx, server_name: str, *, fc_name: str):
        """Search for a Free Company in the FFXIV database based on server and FC name."""
        api_key = await self.get_api_key()
        url = f"{self.base_url}/freecompany/search?name={fc_name}&server={server_name}&private_key={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if 'Results' in data and data['Results']:
            fc = data['Results'][0]
            fc_id = fc['ID']

            detailed_url = f"{self.base_url}/freecompany/{fc_id}?extended=1&private_key={api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(detailed_url) as detailed_response:
                    detailed_data = await detailed_response.json()

            fc_name = detailed_data['FreeCompany']['Name']
            fc_server = detailed_data['FreeCompany']['Server']
            fc_tag = detailed_data['FreeCompany']['Tag']
            fc_slogan = detailed_data['FreeCompany']['Slogan']
            fc_image = detailed_data['FreeCompany']['Crest'][1]
            fc_active_members = detailed_data['FreeCompany']['ActiveMemberCount']
            fc_rank = detailed_data['FreeCompany']['Rank']
            fc_formed = detailed_data['FreeCompany']['Formed']

            embed = discord.Embed(
                title=fc_name,
                description=f"Tag: {fc_tag} | Server: {fc_server}",
                url=f"https://na.finalfantasyxiv.com/lodestone/freecompany/{fc_id}/"
            )
            embed.set_thumbnail(url=fc_image)
            embed.add_field(name="Slogan", value=fc_slogan, inline=False)
            embed.add_field(name="Active Members", value=str(fc_active_members), inline=True)
            embed.add_field(name="Rank", value=str(fc_rank), inline=True)
            embed.add_field(name="Formed", value=str(fc_formed), inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("Free Company not found.")

    @commands.command()
    async def savechar(self, ctx, server_name: str, *, character_name: str):
        """Save your FFXIV character details."""
        await self.config.user(ctx.author).server.set(server_name)
        await self.config.user(ctx.author).character_name.set(character_name)
        await ctx.send(f"Saved {character_name} from {server_name} as your character.")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def me(self, ctx):
        """Retrieve and display your FFXIV character details."""
        server_name = await self.config.user(ctx.author).server()
        character_name = await self.config.user(ctx.author).character_name()

        if server_name and character_name:
            await self.char(ctx, server_name, character_name=character_name)
        else:
            await ctx.send("You haven't saved any character details. Use `.whoami <server> <character name>` to save your character details.")
            
    @char.error
    @csearch.error
    @me.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            raise commands.CommandOnCooldown