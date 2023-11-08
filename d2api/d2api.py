import discord
import asyncio
from random import choice
import re
from redbot.core import commands
from bs4 import BeautifulSoup

import aiohttp
from aiocache import cached

from .d2scrape import BASE_URL, ITEM_URLS
from .d2const import properties, color_code

class D2Scraper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @cached(ttl=3600)
    async def fetch_html(self, url):
        async with self.session.get(url) as response:
            return await response.text()

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def d2item(self, ctx, *, item_name: str):
        item_name = item_name.lower()

        for item_url in ITEM_URLS:
            try:
                html = await self.fetch_html(item_url)
            except Exception as e:
                await ctx.send(f"Error fetching data: {e}")
                return

            soup = BeautifulSoup(html, "html.parser")

            rows = soup.find_all("tr")

            embed_colors = [
                discord.Color.blue(),
                discord.Color.green(),
                discord.Color.orange(),
                discord.Color.purple(),
                discord.Color.red(),
                discord.Color.teal()
            ]

            for row in rows:
                item_name_element = row.find("b")
                if item_name_element:
                    current_item_name = item_name_element.text.strip().lower()
                    if item_name in current_item_name:
                        raw_info = row.get_text(separator='\n')
                        item_info = [line for line in raw_info.split('\n') 
                                    if any(prop in line.lower() for prop in properties) or "-" in line]

                        colored_elements = row.find_all("font", {"color": re.compile(color_code, re.I)})
                        colored_info = [element.get_text() for element in colored_elements]
                        item_info.extend(colored_info)

                        img_element = row.find("img")
                        if img_element:
                            item_image_url = BASE_URL + img_element["src"]
                        else:
                            item_image_url = None

                        title = current_item_name.split(" ")
                        title = " ".join(word.capitalize() for word in title)
                        random_color = choice(embed_colors)
                        embed = discord.Embed(title=title, url=item_url, color=random_color)
                        if item_image_url:
                            embed.set_thumbnail(url=item_image_url)
                        if item_info:
                            item_info_str = "\n".join(item_info)
                            embed.description = item_info_str
                        embed.set_footer(text="Powered by The Arreat Summit")
                        await ctx.send(embed=embed)
                        return

        await ctx.send(f"Item '{item_name}' not found in the database.")