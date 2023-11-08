from .ffxiv import Lodestone

async def setup(bot):
    await bot.add_cog(Lodestone(bot))