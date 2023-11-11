import discord
from redbot.core import commands, Config
from discord.ext import tasks
import requests

# Use at your own risk, this is still experimental!

BATTLEMETRICS_SERVER_ID = "1234567890"
DISCORD_CHANNEL_ID = 1234567890
EMBED_IMAGE_URL = "https://google.com"
DEBUG_CHANNEL_ID = 1234567890
BEARER_TOKEN = "1234567890"

class BattleMetricsAPI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_global(server_info_message_id=None)
        self.update_server_info.start()

    async def send_debug_message(self, message):
        debug_channel = self.bot.get_channel(DEBUG_CHANNEL_ID)
        if debug_channel:
            await debug_channel.send(message)

    @tasks.loop(minutes=30)
    async def update_server_info(self):
        try:
            # The public header does not work, had to grab private one from developer account.
            headers = {
                'Authorization': f'Bearer {BEARER_TOKEN}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f"https://api.battlemetrics.com/servers/{BATTLEMETRICS_SERVER_ID}", headers=headers)

            if response.status_code == 200:
                data = response.json()
                server_info = data.get('data', {}).get('attributes', {})

                embed = discord.Embed(title="Server Info", color=0x00ff00)
                embed.add_field(name="Server Name", value=server_info.get('name', 'N/A'))
                embed.add_field(name="Players Online", value=f"{server_info.get('players', 0)}/{server_info.get('maxPlayers', 0)}")
                embed.add_field(name="Map", value=server_info.get('details', {}).get('map', 'N/A'))
                embed.set_image(url=EMBED_IMAGE_URL)

                if 'modNames' in server_info.get('details', {}) and 'modLinks' in server_info.get('details', {}):
                    mod_strings = [f"[{mod_name}]({mod_link})" for mod_name, mod_link in zip(server_info['details']['modNames'], server_info['details']['modLinks'])]
                    mod_text = ""
                    field_count = 0
                    for mod_string in mod_strings:
                        if len(mod_text) + len(mod_string) + 1 > 1024:  # New line method?
                            embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                            mod_text = mod_string + "\n"
                            field_count += 1
                        else:
                            mod_text += mod_string + "\n"
                    if mod_text:
                        embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                else:
                    embed.add_field(name="Mods", value="No mod information available", inline=False)

                channel = self.bot.get_channel(DISCORD_CHANNEL_ID)
                if channel is None:
                    await self.send_debug_message("Channel not found!")  # I love my debugs
                    return

                message_id = await self.config.server_info_message_id()

                if message_id:
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.edit(embed=embed)
                    except discord.NotFound:
                        message = await channel.send(embed=embed)
                        await self.config.server_info_message_id.set(message.id)
                else:
                    message = await channel.send(embed=embed)
                    await self.config.server_info_message_id.set(message.id)

        except Exception as e:
            await self.send_debug_message(f"Error updating server info: {e}")  # More debugging

    @update_server_info.before_loop
    async def before_update_server_info(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.update_server_info.cancel()